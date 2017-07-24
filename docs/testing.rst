Testing
=======

The unit tests can be triggered by manage.py test

However its hard to test that the user interface renders correctly, in code tests,

So we should write up some test cases.

Manual Testing
--------------

The main landing page is

<site>/library/

There should be a list of libraries and affilations.

Clicking on an affiliation should filter the list of libraries by that affiliation.

Clicking on 'not run' under the heading Library Index should filter out
all libraries that have been run on a flowcell.

Clicking on a library that shows a number in the single or paired
column, should take you to the library page.

Clicking on a library that was sequenced should show a flowcell listed in flowcell notes.

(the raw result files & lane summary statistics sections need to be fixed)

Clicking on a flowcell should show you all of the libraries that were run on it.

<now log in>

The header should show "Welcome <user>, change password / Log out

Clicking on a library ID should take you to the detail page. Next to
the library ID there should now be a little pencil.

Clicking on the pencil should take you to the admin page for the library.

Clicking on view site should take you back to the previous public library page.

If the library was sequenced There should also be a pencil in the
flowcell id column of flowcell notes.
