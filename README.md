
# Fibers: knowledge with bones

<div style="text-align: center;">
<a href="https://f.evoevo.org/html/project_tree.html">ProjectTree</a>
</div>

## Installation

Currently, Fibers is not ready for production usage. Please refer to  [Development](https://f.evoevo.org/development) for development usage.

## Development

- In order to use OpenAI API, the environment variables `OPENAI_API_KEY` should be set to your API key.
- PyCharm is recommended.

You can setup your development environment by the following commands. You must install `Moduler` first, because `Fibers` depends on it.
```shell
git clone https://github.com/EvoEvolver/Fibers.git
git clone https://github.com/EvoEvolver/Moduler.git
pip install -e Moduler --config-settings editable_mode=strict
pip install -e Fibers --config-settings editable_mode=strict
```

## Acknowledgement

This project is led by [the matter lab](https://www.matter.toronto.edu/) at the University of Toronto.