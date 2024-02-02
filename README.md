
# Fibers: knowledge with bones

<div style="text-align: center;">
<a href="https://f.evoevo.org/html/project_tree.html">ProjectTree</a>
</div>

## Installation

Currently, Fibers is not ready for production usage. Please refer to  [Development](https://f.evoevo.org/development) for development usage.

## Development

- In order to use OpenAI API, the environment variables `OPENAI_API_KEY` should be set to your API key.
- PyCharm is recommended.


You need to have `node` and `npm` installed for the development environment. For this, you can run
```shell
conda install nodejs
```

You can set up your development environment by the following steps. 
```shell
mkdir EvoEvolver
cd EvoEvolver
git clone https://github.com/EvoEvolver/Fibers.git
git clone https://github.com/EvoEvolver/Moduler.git
git clone https://github.com/EvoEvolver/Forest.git
cd Forest
npm install
cd ..
```

If you are using PyCharm, do the following steps:
- Go to settings -> Project structure
- Add `Moduler`, `Forest` and  `Fibers` to the content roots
- Install the dependencies by `pip`

If you are using VSCode, you can make install the packages by
```shell
pip install -e Moduler
pip install -e Forest
pip install -e Fibers
```

## Acknowledgement

This project is led by [the matter lab](https://www.matter.toronto.edu/) at the University of Toronto.