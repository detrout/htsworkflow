"""
Read the made-for field and split them up into different affiliations
while fixing the different spellings for some of our users
"""
import os

script_dir = os.path.split(__file__)[0]
settings_path = os.path.join(script_dir, 'htsworkflow','frontend')
os.environ['DJANGO_SETTINGS_MODULE'] = 'htsworkflow.frontend.settings'

from htsworkflow.frontend.samples import models as samples

def main():
    # names  ( {'target name': ('current name', 'current name') )
    names = [
      'Unknown',
      'Adam Rosenthal',
      'Adler Dillman',
      'Ali',
      'Ali/EHD',
      'Ali/PWS',
      'Andrew Medina-Marino',
      'Brian Williams',
      'Davidson',
      'Elowitz',
      'Erich Schwarz',
      'Georgi Warinov',
      'Gilberto Desalvo',
      'Gigio',
      'Gordon Kwan',
      'Hudson-Alpha',
      'James Puckett',
      'Jingli Zhang',
      'Ellen Rothenberg',
      'Jose Luis',
      'Katherine Fisher',
      'Meyerowitz',
      'Ryan',
      'Demo',
      'Angela Stathopoulos',
      'Steven Kuntz',
      'Tony',
      'Tristan',
      'Yuling Jiao',
      u'Anil Ozdemir',
    ]

    name_map = {
      '': ('Unknown',) ,
      'Adam Rosenthal': ('Adam Rosenthal',),
      'Adler Dillman': ('Adler Dillman',),
      'Ali': ('Ali',),
      'Ali/EHD': ('Ali/EHD',),
      'Ali/PWS': ('Ali/PWS',),
      'Andrew Medina-Marina': ('Andrew Medina-Marino',),
      'Andrew Medina-Marino': ('Andrew Medina-Marino',),
      'Brian': ('Brian Williams',),
      'Brian Williams': ('Brian Williams',),
      'Davidson': ('Davidson',),
      'Elowitz': ('Elowitz',),
      'Erich Schwarz': ('Erich Schwarz',),
      'Erich Schwartz': ('Erich Schwarz',),
      'Georgi Warinov': ('Georgi Warinov',),
      'Gilberto Desalvo': ('Gilberto Desalvo',),
      'Gordon Kwan': ('Gordon Kwan',),
      'Gordon': ('Gordon Kwan',),
      'Alpha-Hudson': ('Hudson-Alpha',),
      'Hudson-Alpha': ('Hudson-Alpha',),
      'James Puckett': ('James Puckett',),
      'Jingli Zhang, Rothenberg': ('Jingli Zhang', 'Ellen Rothenberg',),
      'Jingli Zhang': ('Jingli Zhang',),
      'Jose Luis': ('Jose Luis',),
      'Katherine Fisher': ('Katherine Fisher',),
      'Katherine, Gigio': ('Katherine Fisher', 'Gigio',),
      'Meyerowitz': ('Meyerowitz',),
      'Ryan, Demo': ('Ryan', 'Demo',),
      'Stathopoulos': ('Angela Stathopoulos',),
      'Steve Kuntz': ('Steven Kuntz',),
      'Steven Kuntz': ('Steven Kuntz',),
      'Tony': ('Tony',),
      'Tristan': ('Tristan',),
      'Yuling Jiao': ('Yuling Jiao',),
      u'Anil Ozdemir': (u'Anil Ozdemir',),
    }

    affiliations = {}
    for name in names:
      aff = samples.Affiliation(name=name)
      affiliations[name] = aff
      aff.save()

    for lib in samples.Library.objects.all():
      made_list = name_map[lib.made_for]
      assert type(made_list) == type((None,))
      affiliation_list = []
      for n in made_list:
        lib.affiliations.add(affiliations[n])
      lib.save()

if __name__ == "__main__":
  print "don't run this unless you know what its for"
  print "it converts the caltech 'made_for' field into a set of"
  print "affiliations."
  print ""
  print "The user lists are hard coded and exist mostly for my"
  print "convienence."
  #main()
