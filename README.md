----*Urdu to other languages Translation service*----
Version 0.4-09252024
Platform: Windows/Linux (Tested on Windows only)

I) Setup instructions:
----------------------
1. Manually Install Python 3.11.2

2. Ensure python path is set in system variables.
If python path is: C:\Users\LENOVO\AppData\Local\Programs\Python\Python311, then ensure below python paths are added in the System variable "Path" under:
	e.g.: C:\Users\LENOVO\AppData\Local\Programs\Python\Python311
	e.g.: C:\Users\LENOVO\AppData\Local\Programs\Python\Python311\Scripts

3. Run the following command: 
	pip install -r requirements.txt

II) Run Instructions:
---------------------
1. Set OpenAI API Key as environment variable: 
	setx OAI_API_KEY "insert-actual-api-key-here"

2. Open command prompt and execute the below commmand:
	command example : python translate_ur_to_other_languages.py translation_conf.cfg ur mr te be // it will run for 15 seconds and then translate to the respective languages in the different txt files in folder live_process.


Note: The last two arguments are two target languages in which the program will translate the audio file. Use below map to provide the correct target locale:
target_language_locale_map --> {'mr': 'Marathi', 'te': 'Telugu', 'be':'Bengali', 'ta':'Tamil', 'ka':'Kannada', 'ma': 'Malayalam', 'ur':'Urdu'}


III) Output:
------------
1. output path: The output will be generated in a new directory for example, live_process 10-8-24, 11:34 (example) 
