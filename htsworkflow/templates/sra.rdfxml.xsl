<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xs="http://www.w3.org/2001/XMLSchema#"
                xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
		xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
                xmlns:submission="http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#"
                xmlns:sra="http://www.ncbi.nlm.nih.gov/sra"
                xmlns:sras="http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-3/SRA.package.xsd#"
                xmlns:sraa="http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-3/SRA.attribute#"
                >

<xsl:output method="xml" indent="yes"/>

<xsl:template match="/">
  <rdf:RDF xmlns:ddf="http://encodesubmit.ucsc.edu/pipeline/download_ddf#"
           xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	   xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
           xmlns:submission="http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#"
           xmlns:pipeline="http://encodesubmit.ucsc.edu/pipeline/"
           xmlns:sra="http://www.ncbi.nlm.nih.gov/sra"
           xmlns:sras="http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-3/SRA.package.xsd#"
           xmlns:sraa="http://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA_1-3/SRA.attribute#"
>
    <xsl:apply-templates select="*"/>
  </rdf:RDF>
</xsl:template>

<xsl:template match="EXPERIMENT_PACKAGE">
  <xsl:apply-templates select="./EXPERIMENT"/>
  <!-- xsl:for-each select="./EXPERIMENT/EXPERIMENT_ATTRIBUTES/EXPERIMENT_ATTRIBUTE">
    <xsl:call-template name="node_detail"/>
  </xsl:for-each -->
  <xsl:apply-templates select="./SUBMISSION"/>
  <xsl:apply-templates select="./STUDY"/>
  <xsl:apply-templates select="./SAMPLE"/>
  <!-- xsl:for-each select="./SAMPLE/SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE">
    <xsl:call-template name="node_detail"/>
  </xsl:for-each -->
  <xsl:apply-templates select="./RUN_SET"/>
</xsl:template>

<xsl:template match="EXPERIMENT">
  <sras:experiment>
    <xsl:attribute name="rdf:about">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
    <sras:experiment_alias><xsl:value-of select="@alias"/></sras:experiment_alias>
    <sras:center_name><xsl:value-of select="@center_name"/></sras:center_name>
    <xsl:apply-templates select="STUDY_REF"/>
    <xsl:apply-templates select="DESIGN"/>
    <xsl:apply-templates select="PLATFORM"/>
    <xsl:for-each select="./EXPERIMENT_ATTRIBUTES/EXPERIMENT_ATTRIBUTE">
      <xsl:call-template name="node_simple"/>
    </xsl:for-each>
    <sras:submission>
      <xsl:attribute name="rdf:resource">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="../SUBMISSION/@accession"/></xsl:attribute>
    </sras:submission>
  </sras:experiment>
</xsl:template>

<xsl:template match="STUDY_REF">
  <sras:study>
    <xsl:attribute name="rdf:resource">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
  </sras:study>
</xsl:template>

<xsl:template match="DESIGN">
  <xsl:apply-templates select="SAMPLE_DESCRIPTOR"/>
  <xsl:apply-templates select="LIBRARY_DESCRIPTOR"/>
</xsl:template>

<xsl:template match="SAMPLE_DESCRIPTOR">
  <sras:sample>
    <xsl:attribute name="rdf:resource">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
  </sras:sample>
</xsl:template>

<xsl:template match="LIBRARY_DESCRIPTOR">
  <sras:library_name><xsl:value-of select="LIBRARY_NAME"/></sras:library_name>
  <sras:library_strategy><xsl:value-of select="LIBRARY_STRATEGY"/></sras:library_strategy>
  <sras:library_source><xsl:value-of select="LIBRARY_SOURCE"/></sras:library_source>
  <sras:library_selection><xsl:value-of select="LIBRARY_SELECTION"/></sras:library_selection>
  <sras:library_protocol>
    <xsl:attribute name="rdf:resource">http:<xsl:value-of select="substring-after(LIBRARY_CONSTRUCTION_PROTOCOL, 'http')"/></xsl:attribute></sras:library_protocol>
</xsl:template>

<xsl:template match="PLATFORM">
  <sras:instrument_model><xsl:value-of select="ILLUMINA/INSTRUMENT_MODEL"/></sras:instrument_model>
  <sras:sequence_length rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal"><xsl:value-of select="ILLUMINA/SEQUENCE_LENGTH"/></sras:sequence_length>
</xsl:template>

<!-- xsl:template select="EXPERIMENT" mode="ref" -->
<xsl:template name="node_ref">
  <sras:has_attribute>
    <xsl:attribute rdf:name="rdf:nodeID"><xsl:value-of select="generate-id(node())"/></xsl:attribute>
  </sras:has_attribute>
</xsl:template>

<!-- xsl:template name="attribute" mode="nodedetail" -->
<xsl:template name="node_detail">
  <sras:attribute>
    <xsl:attribute rdf:name="rdf:nodeID"><xsl:value-of select="generate-id(node())"/></xsl:attribute>
    <sras:attribute_name><xsl:value-of select="TAG"/></sras:attribute_name>
  </sras:attribute>
  <sras:attribute>
    <xsl:attribute rdf:name="rdf:nodeID"><xsl:value-of select="generate-id(node())"/></xsl:attribute>
    <sras:attribute_value><xsl:value-of select="VALUE"/></sras:attribute_value>
  </sras:attribute>
</xsl:template>

<!-- try to generate attributes with non blank nodes -->
<xsl:template name="node_simple">
  <xsl:variable name="spacelessTag">
    <xsl:call-template name="string-replace-all">
      <xsl:with-param name="text" select="TAG" />
      <xsl:with-param name="replace" select="' '" />
      <xsl:with-param name="by" select="'_'" />
    </xsl:call-template>
  </xsl:variable>
  <xsl:element name="sraa:{$spacelessTag}"><xsl:value-of select="VALUE"/></xsl:element>
</xsl:template>

<!-- SUBMISSION TOP LEVEL -->
<xsl:template match="SUBMISSION">
  <sras:submission>
    <xsl:attribute name="rdf:about">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
    <sras:alias><xsl:value-of select="@alias"/></sras:alias>
    <sras:comment><xsl:value-of select="@submission_comment"/></sras:comment>
    <sras:date rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime"><xsl:value-of select="@submission_date"/></sras:date>
    <sras:lab_name><xsl:value-of select="@lab_name"/></sras:lab_name>
    <sras:accession><xsl:value-of select="@accession"/></sras:accession>
  </sras:submission>
</xsl:template>

<xsl:template match="STUDY">
  <sras:study>
    <xsl:attribute name="rdf:about">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
    <sras:study_alias><xsl:value-of select="@alias"/></sras:study_alias>
    <sras:title><xsl:value-of select="DESCRIPTOR/STUDY_TITLE"/></sras:title>
    <sras:description><xsl:value-of select="normalize-space(DESCRIPTOR/STUDY_DESCRIPTION)"/></sras:description>
  </sras:study>
</xsl:template>

<xsl:template match="SAMPLE">
  <sras:sample>
    <xsl:attribute name="rdf:about">http://www.ncbi.nlm.nih.gov/sra/<xsl:value-of select="@accession"/></xsl:attribute>
    <sras:sample_alias><xsl:value-of select="@alias"/></sras:sample_alias>
    <sras:common_name><xsl:value-of select="SAMPLE_NAME/COMMON_NAME"/></sras:common_name>
    <sras:description><xsl:value-of select="DESCRIPTION"/></sras:description>
    <xsl:for-each select="./SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE">
      <xsl:call-template name="node_simple"/>
    </xsl:for-each>
  </sras:sample>
</xsl:template>
<xsl:template match="RUN_SET">
</xsl:template>

<!-- from http://geekswithblogs.net/Erik/archive/2008/04/01/120915.aspx -->
<xsl:template name="string-replace-all">
    <xsl:param name="text" />
    <xsl:param name="replace" />
    <xsl:param name="by" />
    <xsl:choose>
      <xsl:when test="contains($text, $replace)">
        <xsl:value-of select="substring-before($text,$replace)" />
        <xsl:value-of select="$by" />
        <xsl:call-template name="string-replace-all">
          <xsl:with-param name="text"
          select="substring-after($text,$replace)" />
          <xsl:with-param name="replace" select="$replace" />
          <xsl:with-param name="by" select="$by" />
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
