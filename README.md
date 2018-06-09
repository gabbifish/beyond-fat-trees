# Beyond Fat-Trees Replication Readme

### Setup
This code has only been tested on Linux Debian 4.9, but should also work on latest versions of Ubuntu or Debian.

First, you must install mininet:
```
apt-get install mininet
```

Then, download pox in the same directory as mininet:
```
git clone https://github.com/noxrepo/pox
```

Ensure you have pip, the python package manager installed:
```
apt-get install pip
```

Copy the contents of this github repository into pox/ext.

Finally, run the following to download any final python dependencies:
```
pip install -r requirements.txt
```

### Generating Figures
Run the simulate_graphs.sh script
```
sh simulate_graphs.sh
```
