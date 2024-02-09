# Get file path
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# go the parent directory
ProjectRoot=$DIR/../..

# check if ProjectRoot/EvoEvolver exists
if [ -d "$ProjectRoot/Moduler" ]; then
  echo "Updating Moduler"
  git pull
else
  echo "Moduler does not exist"
  exit 1
fi

if [ -d "$ProjectRoot/Forest" ]; then
  echo "Forest exists"
  git pull
else
  echo "Forest does not exist"
  exit 1
fi