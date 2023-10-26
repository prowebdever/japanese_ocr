1. extract the text from pdf.
  	python azure.py [folder path that contains pdf files]
	
	when you run the above command, the text will be stored 'ocr' folder.
	this program requires an Azure API, so you must be connected to the internet.

2. analyze the text
	python extract.py

	this program requires output from azure.py. So you need to run azure.py first.