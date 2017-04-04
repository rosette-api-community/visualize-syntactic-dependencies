# Visualizing Dependency Parse Trees

## Introduction
This repository includes a Python script that can produce graphical renderings of the dependency parse trees as returned by the [Rosette API `syntax/dependencies` endpoint](https://developer.rosette.com/features-and-functions#introduction17).  The script relies on [GraphViz](http://graphviz.org/) to produce SVG image files that can be viewed in a web browser.

## Installation
### Python Dependencies
The Python script `deps_to_graph.py` is written for Python 3 (specifically Python 3.6.0, but should be compatible with most versions of Python 3).  To install the Python dependencies it's recommended to setup a virtual environment with `virtualenv`.  To begin, make sure [`virtualenv`](https://virtualenv.pypa.io/en/stable/installation/) is installed and up to date with [`pip`](https://pip.pypa.io/en/stable/installing/):

    $ pip3 install -U virtualenv

Create a virtual environment in the current directory:

    $ python3 $(which virtualenv) .

Then, activate the virtual environment:

    $ source bin/activate

Finally, install the Python 3 dependences from the `requirements.txt` file:

    (parse_tree_viz) $ pip3 install -r requirements.txt

### GraphViz
`deps_to_graph.py` relies on the `dot` program from the [GraphViz](http://graphviz.org/) package to produce SVG images, so the last step is to install GraphViz.  GraphViz can be installed from most popular managers ([Homebrew](https://brew.sh/), [RPM](http://rpm.org/), etc.).  Once you've installed the GraphViz package, you can check if the `dot` binary is available:

    $ which dot

If the above command prints a path to the `dot` binary, and you've followed the earlier steps to install the Python dependencies, then you're all set to start visualizing some dependency parse trees!

## Usage
This section describes how to use `deps_to_graph.py`:

    $ ./deps_to_graph.py -h
    usage: deps_to_graph.py [-h] [-i INPUT] [-u] [-o OUTPUT] [-k KEY] [-a API_URL]
                            [-l LANGUAGE] [-b]
    
    Render Rosette API dependency parse trees as SVG via Graphviz
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            Path to a file containing input data (if not specified
                            data is read from stdin) (default: None)
      -u, --content-uri     Specify that the input is a URI (otherwise load text
                            from file) (default: False)
      -o OUTPUT, --output OUTPUT
                            Path to a file where SVG will be written (if not
                            specified data is written to stdout) (default: None)
      -k KEY, --key KEY     Rosette API Key (default: None)
      -a API_URL, --api-url API_URL
                            Alternative Rosette API URL (default:
                            https://api.rosette.com/rest/v1/)
      -l LANGUAGE, --language LANGUAGE
                            A three-letter (ISO 639-2 T) code that will override
                            automatic language detection (default: None)
      -b, --label-indices   Add token index labels to show the original token
                            order; this can help in reading the trees, but it adds
                            visual clutter (default: False)
    

The script takes input, makes a request to the Rosette API on your behalf, and converts the resulting JSON into an SVG image.  The SVG data is written to `/dev/stdout` by default, or to the given file path specified with the `-o/--output` option.

Note: If you want to circumvent supplying your [Rosette API key](https://developer.rosette.com/) with `-k/--key` (or typing it at the prompt) on every execution of the script, you can set a `ROSETTE_USER_KEY` enviroment variable:

    $ echo "export ROSETTE_USER_KEY=<your-user-key>" >> ~/.bash_profile
    $ . ~/.bash_profile

### Examples
`deps_to_graph.py` can read input from `/dev/stdin`, a file path, or a URI.

#### Reading from `stdin`

    $ echo "Let's make a graph" | ./deps_to_graph.py > graph.svg
    
You can look at the resulting `graph.svg` by opening it in your web browser.

It will look like this:

![graph.svg](https://cdn.rawgit.com/rosette-api-community/visualize-syntactic-dependencies/ab441bd3/svgs/graph.svg)

#### Reading from a file

	# create a sample text file to read from
	$ echo "The rules governing the hierarchical structure of a sentence are called “syntax” in linguistics. Knowing the structure of a sentence helps to understand how the words in a sentence are related to each other." > data.txt
	# create an SVG visualization using the content of the text file as input
	$ ./deps_to_graph.py -i data.txt > data.svg

The results will look like this:

![data.svg](https://cdn.rawgit.com/rosette-api-community/visualize-syntactic-dependencies/ab441bd3/svgs/data.svg)

#### Reading from a URI

Another option is to rely on Rosette API to extract the textual content of a web page and parse it.  You can do this by giving a URI with the `-i/--input` option and additionally specifying the `-u/--content-uri` option to indicate that the input is a URI:

	$ ./deps_to_graphy.py -u -i 'www.your-favorite-site.com' > your-favorite-site.svg
	
### Token index labels
One additional convenience option is the `-b/--label-indices` option.  This labels each node in the parse tree with an index.  This can help with reading the content from the graph as it shows the original order of the word tokens.  This is left off by default as it adds visual clutter, but it can be a useful option:

	$ ./deps_to_graph.py -b -i data.txt > labeled-data.svg

With token index labels, the trees looks like this:

![labeled-data.svg](https://cdn.rawgit.com/rosette-api-community/visualize-syntactic-dependencies/ab441bd3/svgs/labeled-data.svg)