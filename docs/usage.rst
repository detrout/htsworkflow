Web Database
============

Manual setup
------------

You'll need to create some users and "affiliations". users can
belong to affiliations, and affiliations can be attached to libraries.

Affiliations usually represent labs and will be the core of the
permissions system whenever its implemented.

We created affilations to represent labs or projects.

You may need to fill in species, library types, multiplex indicies,
sequencers, and cluster stations tables before creating libraries and
flowcells as well.

Normal usage
------------

To create a new library or flowcell go to `/admin/` and select either
add for either of them.

Once a flowcell is created you can send a "started" email to everyone
who needs to be notified of an upcoming flowcell.

It'll send email to the affiliation address and any user email
addresses added.
