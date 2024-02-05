conda create -n Evo python=3.10
conda activate Evo # You can replace the name
# Check whether nodejs is installed
if which node > /dev/null
then
  echo "node is installed"
else
  echo "node is not installed"
  echo "Installing nodejs"
  conda install nodejs
fi
mkdir EvoEvolver # Create the folder for the projects
cd EvoEvolver
git clone https://github.com/EvoEvolver/Moduler.git
git clone https://github.com/EvoEvolver/Forest.git
git clone https://github.com/EvoEvolver/Fibers.git
pip install -e Moduler
pip install -e Forest
pip install -e Fibers