# ASCII-Adapter
Converts images to coloured ASCII text  
## See our other project done in parallel which takes [GIFs and creates the same thing in text form.](https://github.com/tiffxnychiu/GIF-to-ASCII)

*Done in Python*

Created by University of Waterloo first and second year CS students:  

Mark Chen - Lead Software Engineer  
Bonnie Peng - Software Engineer  
Ted Weng - Software Engineer  
Tiffany Chiu - Software Engineer  
Nicole Shi - Software Engineer


## Demonstration
### Original
<p align="center"><img width=50% src="https://github.com/marko-polo-cheno/Abstract-ASCII-Adapter/blob/main/calcifer.jpg"></p>

### HTML output
<p align="center"><img width=50% src="https://github.com/marko-polo-cheno/Abstract-ASCII-Adapter/blob/main/calcified.png"></p>

https://htmlpreview.github.io/?https://github.com/marko-polo-cheno/Abstract-ASCII-Adapter/blob/main/outputcalcifer.html

## Usage:

```
python imgToText.py calcifer.jpg --maxHeight=60 -c -a --char=@ --heightRatio=0.6
```

## Dependencies:

```
pip install Pillow>=8.0.1
pip install docopt>=0.6.2
```
