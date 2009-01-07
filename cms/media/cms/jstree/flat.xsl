<?xml 
	version="1.0" 
	encoding="utf-8" 
	?>
<xsl:stylesheet 
	version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	>
<xsl:output 
	method="html" 
	encoding="utf-8" 
	omit-xml-declaration="yes" 
	standalone="no" 
	indent="no" 
	media-type="text/xml" 
	/>

<xsl:param name="theme_name" />
<xsl:param name="theme_path" />

<xsl:template match="/">
	<ul>
	<xsl:if test="$theme_name"><xsl:attribute name="class"><xsl:value-of select="$theme_name" /></xsl:attribute></xsl:if>
	<xsl:for-each select="//item[not(@parent_id) or @parent_id=0]">
		<xsl:call-template name="nodes">
			<xsl:with-param name="node" select="." />
			<xsl:with-param name="theme_path" select="$theme_path" />
		</xsl:call-template>
	</xsl:for-each>
	</ul>
</xsl:template>

<xsl:template name="nodes">
	<xsl:param name="node" />
	<xsl:param name="theme_path" />

	<xsl:variable name="children" select="count(//item[@parent_id=$node/attribute::id]) &gt; 0" />
	
	<li>
	<xsl:attribute name="class">
		<xsl:if test="position() = last()"> last </xsl:if>
		<xsl:choose>
			<xsl:when test="@state = 'open'"> open </xsl:when>
			<xsl:when test="$children or @hasChildren"> closed </xsl:when>
			<xsl:otherwise> leaf </xsl:otherwise>
		</xsl:choose>
		<xsl:value-of select="@class" />
	</xsl:attribute>
	<xsl:for-each select="@*">
		<xsl:if test="name() != 'parent_id' and name() != 'hasChildren' and name() != 'class' and name() != 'state'">
			<xsl:attribute name="{name()}"><xsl:value-of select="." /></xsl:attribute>
		</xsl:if>
	</xsl:for-each>
	<xsl:for-each select="content/name">
		<a href="#">
		<xsl:attribute name="class"><xsl:value-of select="@lang" /> <xsl:value-of select="@class" /></xsl:attribute>
		<xsl:attribute name="style">
			<xsl:value-of select="@style" />
			<xsl:if test="string-length(attribute::icon) > 0">background-image:url(<xsl:if test="not(contains(@icon,'/'))"><xsl:value-of select="$theme_path" /></xsl:if><xsl:value-of select="@icon" />);</xsl:if>
		</xsl:attribute>
		<xsl:for-each select="@*">
			<xsl:if test="name() != 'style' and name() != 'class'">
				<xsl:attribute name="{name()}"><xsl:value-of select="." /></xsl:attribute>
			</xsl:if>
		</xsl:for-each>
		<xsl:value-of select="." /></a>
	</xsl:for-each>
	<xsl:if test="$children or @hasChildren">
		<ul>
			<xsl:for-each select="//item[@parent_id=$node/attribute::id]">
				<xsl:call-template name="nodes">
					<xsl:with-param name="node" select="." />
					<xsl:with-param name="theme_path" select="$theme_path" />
				</xsl:call-template>
			</xsl:for-each>
		</ul>
	</xsl:if>
	</li>
</xsl:template>
</xsl:stylesheet>