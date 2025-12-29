<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" 
	xmlns:odm="http://www.cdisc.org/ns/odm/v1.2" 
	xmlns:def20="http://www.cdisc.org/ns/def/v2.0" 
	xmlns:def21="http://www.cdisc.org/ns/def/v2.1" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	
<xsl:output method="text" version="1.0" encoding="UTF-8" indent="yes"/>

<!-- Root of the metadata -->
<xsl:variable name="root" select="/odm:ODM"/> 
	
<!-- Variables -->
<xsl:variable name="lf" select="'&#xA;'"/> 

<!-- Parameters -->
<xsl:param name="dsName"/>
<xsl:param name="datasetJSONCreationDateTime" select="'9999-01-01T00:00:00'"/>
	
<xsl:template match="/"> 
	<xsl:text>{</xsl:text>
	<xsl:text>&quot;datasetJSONCreationDateTime&quot;: &quot;</xsl:text> <xsl:value-of select="$datasetJSONCreationDateTime"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;datasetJSONVersion&quot;: &quot;1.1.0&quot;</xsl:text>
	<xsl:text>, &quot;studyOID&quot;: &quot;</xsl:text> <xsl:value-of select="normalize-space($root/odm:Study/@OID)"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;metaDataVersionOID&quot;: &quot;</xsl:text> <xsl:value-of select="normalize-space($root/odm:Study/odm:MetaDataVersion/@OID)"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;itemGroupOID&quot;: &quot;</xsl:text> <xsl:value-of select="$root/odm:Study/odm:MetaDataVersion/odm:ItemGroupDef[upper-case(@Name)=upper-case($dsName)]/@OID"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;records&quot;: 0</xsl:text>
	<xsl:text>, &quot;name&quot;: &quot;</xsl:text> <xsl:value-of select="$root/odm:Study/odm:MetaDataVersion/odm:ItemGroupDef[upper-case(@Name)=upper-case($dsName)]/@Name"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;label&quot;: &quot;</xsl:text> <xsl:value-of select="$root/odm:Study/odm:MetaDataVersion/odm:ItemGroupDef[upper-case(@Name)=upper-case($dsName)]/odm:Description/odm:TranslatedText"/> <xsl:text>&quot;</xsl:text>
	<xsl:text>, &quot;columns&quot;: [</xsl:text>
	
    <xsl:for-each select="$root/odm:Study/odm:MetaDataVersion/odm:ItemGroupDef[upper-case(@Name)=upper-case($dsName)]/odm:ItemRef">
        <xsl:variable name="ItemOID" select="@ItemOID"/>
        <xsl:variable name="Name" select="$root/odm:Study/odm:MetaDataVersion/odm:ItemDef[@OID=$ItemOID]/@Name"/>
        <xsl:variable name="DataType" select="$root/odm:Study/odm:MetaDataVersion/odm:ItemDef[@OID=$ItemOID]/@DataType"/>
        <xsl:variable name="Label" select="$root/odm:Study/odm:MetaDataVersion/odm:ItemDef[@OID=$ItemOID]/odm:Description/odm:TranslatedText"/>
        <xsl:variable name="Length" select="$root/odm:Study/odm:MetaDataVersion/odm:ItemDef[@OID=$ItemOID]/@Length"/>
        <xsl:variable name="DisplayFormat" select="$root/odm:Study/odm:MetaDataVersion/odm:ItemDef[@OID=$ItemOID]/(@def20:DisplayFormat|@def21:DisplayFormat)"/>
        <xsl:variable name="KeySequence" select="@KeySequence"/>
        <xsl:variable name="dataType">
			<xsl:choose>
				<xsl:when test="$DataType = 'text' or $DataType = 'datetime' or $DataType = 'date' or $DataType = 'time' or $DataType = 'partialDate' or $DataType = 'partialTime' or
								$DataType = 'partialDatetime' or $DataType = 'incompleteDatetime' or $DataType = 'durationDatetime' or $DataType = 'intervalDatetime'">
					<xsl:text>string</xsl:text>
				</xsl:when>
				<xsl:when test="$DataType = 'integer' and matches($Name, '^[A-Z][A-Z0-9_]{0,4}DTM$')">
					<xsl:text>datetime</xsl:text>
				</xsl:when>				
				<xsl:when test="$DataType = 'integer' and matches($Name, '^[A-Z][A-Z0-9_]{0,5}DT$')">
					<xsl:text>date</xsl:text>
				</xsl:when>				
				<xsl:when test="$DataType = 'integer' and matches($Name, '^[A-Z][A-CE-Z0-9_]{0,5}TM$') and not(matches($Name, '^[A-Z][A-Z0-9_]{0,3}RLTM$')) and not(matches($Name, '^[A-Z][A-Z0-9_]{0,3}ELTM$'))">
					<xsl:text>time</xsl:text>
				</xsl:when>				
				<xsl:otherwise>
					<xsl:value-of select="$DataType"/>
				</xsl:otherwise>
			</xsl:choose> 
        </xsl:variable>
        <xsl:variable name="targetDataType">
			<xsl:choose>
				<xsl:when test="$DataType = 'decimal'">
					<xsl:text>decimal</xsl:text>
				</xsl:when>
				<xsl:when test="($DataType = 'integer' and matches($Name, '^[A-Z][A-Z0-9_]{0,4}DTM$')) or
				                ($DataType = 'integer' and matches($Name, '^[A-Z][A-Z0-9_]{0,5}DT$')) or
				                ($DataType = 'integer' and matches($Name, '^[A-Z][A-CE-Z0-9_]{0,5}TM$') and not(matches($Name, '^[A-Z][A-Z0-9_]{0,3}RLTM$')) and not(matches($Name, '^[A-Z][A-Z0-9_]{0,3}ELTM$')))">
					<xsl:text>integer</xsl:text>
				</xsl:when>				
				<xsl:otherwise>
					<xsl:text></xsl:text>
				</xsl:otherwise>
			</xsl:choose> 
        </xsl:variable>
		<xsl:text>{</xsl:text> 
		<xsl:text>&quot;itemOID&quot;: &quot;</xsl:text> <xsl:value-of select="$ItemOID"/> <xsl:text>&quot;</xsl:text>
		<xsl:text>, &quot;name&quot;: &quot;</xsl:text> <xsl:value-of select="$Name"/> <xsl:text>&quot;</xsl:text>
		<xsl:text>, &quot;label&quot;: &quot;</xsl:text> <xsl:value-of select="$Label"/> <xsl:text>&quot;</xsl:text>
		<xsl:text>, &quot;dataType&quot;: &quot;</xsl:text> <xsl:value-of select="$dataType"/> <xsl:text>&quot;</xsl:text>
		<xsl:if test="$targetDataType != ''">
			<xsl:text>, &quot;targetDataType&quot;: &quot;</xsl:text> <xsl:value-of select="$targetDataType"/> <xsl:text>&quot;</xsl:text>
		</xsl:if>
		<xsl:if test="$Length">
			<xsl:text>, &quot;length&quot;: </xsl:text> <xsl:value-of select="$Length"/>
		</xsl:if>
		<xsl:if test="$DisplayFormat">
			<xsl:text>, &quot;displayFormat&quot;: &quot;</xsl:text> <xsl:value-of select="$DisplayFormat"/> <xsl:text>&quot;</xsl:text>
		</xsl:if>
		<xsl:if test="$KeySequence">
			<xsl:text>, &quot;keySequence&quot;: </xsl:text> <xsl:value-of select="$KeySequence"/>
		</xsl:if>
		<xsl:text>}</xsl:text> 
		<xsl:if test="position() != last()">
			<xsl:text>, </xsl:text>
		</xsl:if>
    </xsl:for-each>
    
	<xsl:text>], &quot;rows&quot;: []</xsl:text>
	<xsl:text>}</xsl:text>
</xsl:template> 
	
</xsl:stylesheet>