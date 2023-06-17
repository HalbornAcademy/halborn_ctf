.. _faq:

Halborn CTF FAQ
===============

This is a list of Frequently Asked Questions about ``halborn-ctf``.  Feel free to
suggest new entries!

How do I...

Create private deployments
^^^^^^^^^^^^^^^^^^^^^^^^^^

    If you don't want to show any of the deployment process to the player: 

    - Set the ``HAS_FILES`` to ``False``. 
    - Probably you want the ``HAS_DETAILS`` set to ``True`` to display information on how to interact with your challenge.

    If you don't want to show any of the deployment process at all to the player but still want to provide files:

    - Set the ``HAS_FILES`` to ``True``. And list the files that you want the player to have.
    - Create a separated script/file and use it on your Dockerfile. 
    - Make sure this private file is not exposed. 

.. note::
    Keep in mind that if no files are exposed under ``file`` the ``challenge.py`` script does only give a hint on how the challenge was deployed.

Create temporary files from strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. code::

    from halborn_ctf.templates import StrFile

    ...

    def files(self):
        return [
            StrFile('folder/test.txt', 'THIS IS THE CONTENT')
        ]
