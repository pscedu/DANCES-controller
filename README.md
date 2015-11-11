# DANCES-controller

Centralized Ryu controller for the DANCES project.

### Installing Ryu

Installing from source:

```
$ git clone git://github.com/osrg/ryu.git
$ cd ryu; python ./setup.py install 
```

Installing using pip:

```
$ pip install ryu
```

### Running

Run with ryu-manager (uses valve.yaml from the current working directory):

```
$ ryu-manager valve.py
```
