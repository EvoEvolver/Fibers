from fibers.compose.pipeline_code import tool_box
from fibers.compose.pipeline_code.instruction_runner import InstructionRunner
from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree
from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.helper.cache.cache_service import caching


def main():

    import data_analyst_lab

    instructions = """
# Data generation
Generate experiment data with noise scale being 0.01
Generate the plot of the experiment data
# Data display
Display the plot of experiment data
"""

    tree = markdown_to_tree(instructions)

    preprocess_text_tree(tree, fat_limit=300)

    inst_runner = InstructionRunner([data_analyst_lab, tool_box], None)

    inst_runner.grow_instruction_tree(tree.root.first_child())

    caching.save_used()


if __name__ == '__main__':
    main()