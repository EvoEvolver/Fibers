# Get file path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# go the parent directory
ProjectRoot=$DIR/../..

cd $ProjectRoot/Fibers && git pull

# check if ProjectRoot/EvoEvolver exists
if [ -d "$ProjectRoot/Moduler" ]; then
  echo "Updating Moduler"
  cd $ProjectRoot/Moduler && git pull
else
  echo "Moduler does not exist"
  exit 1
fi

if [ -d "$ProjectRoot/Forest" ]; then
  echo "Forest exists"
  cd $ProjectRoot/Forest && git pull
else
  echo "Forest does not exist"
  exit 1
fi