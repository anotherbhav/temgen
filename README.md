# temren
- Network Template Renderer - A CLI network [tem]plate [ren]derer takes variables (from a YAML) a template (from a JINJA2) and smooshes them together and renders the result

# Requirements
- python3
- python modules [ pyyaml jinja2 ]

Assuming you are on OSX and have brew, you can do something like the following to meet the requirements

  brew install python3
  pip3 install pyyaml jinja2


# Getting Started

Clone This Repo:

    git clone https://github.com/anotherbhav/temren.git


List sample Templates

    ./temren.py --list


Render A Template:

    ./temren.py --config sample1_cisco_uplinks.yaml
