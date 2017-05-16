Script to navigate the AIB website

Draft, relying on selenium

    virtualenv venv
    pip install -r requirements.txt

Note: this may break at any time due to layout changes in the AIB site.

Create the CREDENTIALS.json file, looking like this:

    {
      "registration_number": "XXXXXXXX",
      "pac": null
    }

The pac (personal access code) can be set in the file, as an environment variable, or type it at runtime.

Have a look at the run.sh script for usage. You'll most likely need to
customize it.
