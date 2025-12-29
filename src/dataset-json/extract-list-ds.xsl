<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" 
	xmlns:odm="http://www.cdisc.org/ns/odm/v1.2" 
	xmlns:def20="http://www.cdisc.org/ns/def/v2.0" 
	xmlns:def21="http://www.cdisc.org/ns/def/v2.1" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	
<xsl:output method="text" version="1.0" encoding="UTF-8" indent="yes"/>

<xsl:template match="/"> 
    <xsl:for-each select="/odm:ODM/odm:Study/odm:MetaDataVersion/odm:ItemGroupDef">
		<xsl:value-of select="normalize-space(@Name)"/>
		<xsl:if test="position() != last()">
			<xsl:text>,</xsl:text>
		</xsl:if>
    </xsl:for-each>
</xsl:template> 
	
</xsl:stylesheet>
