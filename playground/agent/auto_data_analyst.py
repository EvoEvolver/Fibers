from fibers.compose.agent import tool_box
from fibers.compose.agent.instruction_runner import InstructionRunner
from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.helper.cache.cache_service import caching
import data_analyst_lab


def main():

    instructions = """
# Data generation
- Generate experiment data with noise_scale being 0.01
- Generate the figure of the experiment data
# Data display
- Display the image of experiment data
- Ask the vision model what is in the image
"""

    tree = markdown_to_tree(instructions)

    tree.show_tree_gui_react()

    inst_runner = InstructionRunner([data_analyst_lab, tool_box], None)

    inst_runner.run_instruction_tree(tree.root)

    caching.save_used()


if __name__ == '__main__':
    main()