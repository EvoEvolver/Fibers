from fibers.compose.pipeline_code.instruction_runner import InstructionRunner
from fibers.helper.cache.cache_service import caching


def main():
    import data_analyst

    inst_runner = InstructionRunner(data_analyst)

    instruction_list = [
        "Generate experiment data with noise scale being 0.01",
        "Plot the experiment data"
    ]

    inst_runner.run_instructions(instruction_list)

    caching.save_used()


if __name__ == '__main__':
    main()