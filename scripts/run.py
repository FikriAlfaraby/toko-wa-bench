"""Run the tau2 CLI with the toko_wa domain registered and every model call on one endpoint.

tau-bench's language-assertion judge is hard-coded to gpt-4.1 with no endpoint, so LiteLLM would
send it to api.openai.com. Here every OpenAI-format call goes to LLM_BASE_URL, and one judge model
(--judge) reads every run, whichever agent is being tested.

    TAU2_DATA_DIR=../tau2-bench/data LLM_BASE_URL=http://127.0.0.1:20128/v1 LLM_API_KEY=... \\
      uv run python scripts/run.py --judge cx/gpt-6-luna -- run --domain toko_wa \\
      --agent-llm openai/cx/gpt-6-luna --user-llm openai/cx/gpt-6-luna --num-trials 1
"""

import os
import sys


def main() -> None:
    base, key = os.environ.get("LLM_BASE_URL"), os.environ.get("LLM_API_KEY")
    if not base or not key:
        raise SystemExit("set LLM_BASE_URL and LLM_API_KEY")
    if not os.environ.get("TAU2_DATA_DIR"):
        # tau2 installed from git has no data folder: it needs its user-simulator prompts from a clone
        raise SystemExit("set TAU2_DATA_DIR to the data folder of a tau2-bench clone at the pinned commit")
    if "--judge" not in sys.argv or "--" not in sys.argv:
        raise SystemExit(__doc__)
    judge = sys.argv[sys.argv.index("--judge") + 1]
    tau_args = sys.argv[sys.argv.index("--") + 1 :]

    os.environ.update(OPENAI_API_BASE=base, OPENAI_BASE_URL=base, OPENAI_API_KEY=key)
    for name in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        os.environ.pop(name, None)

    # tau2 reads the environment when it is first imported, so it is imported only now.
    import tau2.config as config
    import tau2.evaluator.evaluator_nl_assertions as nl_assertions
    import tau2.orchestrator.orchestrator as orchestrator
    from tau2.cli import main as tau2_main
    from tau2.data_model.message import AssistantMessage

    from toko_wa.register import register

    for module in (config, nl_assertions):
        module.DEFAULT_LLM_NL_ASSERTIONS = f"openai/{judge}"
        module.DEFAULT_LLM_NL_ASSERTIONS_ARGS = {"api_base": base}
    # tau2 opens every chat with an English greeting; a WhatsApp shop opens with its auto-greeting.
    orchestrator.DEFAULT_FIRST_AGENT_MESSAGE = AssistantMessage(
        role="assistant",
        content="Halo Kak, selamat datang di Toko Rapi Bandung. Ada yang bisa dibantu?",
        cost=0.0,
    )
    register()
    sys.argv = ["tau2", *tau_args]
    tau2_main()


if __name__ == "__main__":
    main()
