from fibers.compose.pipeline_code import tool_box
from fibers.compose.pipeline_code.instruction_runner import InstructionRunner, \
    normalize_inst_node
from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree
from fibers.data_loader.markdown_to_tree import markdown_to_tree
from fibers.helper.cache.cache_service import caching
from fibers.helper.utils import parallel_map
from playground.instruction_run import data_analyst_lab


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

    preprocess_text_tree(tree, fat_limit=3000)

    parallel_map(normalize_inst_node, tree.iter_with_dfs())

    tree.show_tree_gui_react()

    inst_runner = InstructionRunner([data_analyst_lab, tool_box], None)

    inst_runner.inst_run_limit = 40

    inst_runner.grow_instruction_tree(tree.root.first_child())

    caching.save_used()


if __name__ == '__main__':
    main()