from xml import sax


def get_cycles(recipe_xml_filepath):
  """
  returns the number of cycles found in Recipe*.xml
  """
  handler = CycleXmlHandler()
  sax.parse(recipe_xml_filepath, handler)
  return handler.cycle_count



class CycleXmlHandler(sax.ContentHandler):

  def __init__(self):
    self.cycle_count = 0
    self.in_protocol = False
    sax.ContentHandler.__init__(self)


  def startDocument(self):
    self.cycle_count = 0
    self.in_protocol = False


  def startElement(self, name, attrs):

    #Only count Incorporations as cycles if within
    # the protocol section of the xml document.
    if name == "Incorporation" and self.in_protocol:
      #print 'Found a cycle!'
      self.cycle_count += 1
      return
    
    elif name == 'Protocol':
      #print 'In protocol'
      self.in_protocol = True
      return

    #print 'Skipping: %s' % (name)
    

  def endElement(self, name):
    
    if name == 'Protocol':
      #print 'End protocol'
      self.in_protocol = False
