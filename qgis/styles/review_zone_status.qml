<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34" styleCategories="Symbology">
  <renderer-v2 type="categorizedSymbol" attr="acceptance_status" enableorderby="0" forceraster="0" symbollevels="0">
    <categories>
      <category value="accepted" label="Accepted review zone" symbol="0" render="true"/>
      <category value="rejected" label="Rejected review zone" symbol="1" render="true"/>
      <category value="" label="Unclassified review zone" symbol="2" render="true"/>
    </categories>
    <symbols>
      <symbol type="fill" name="0" alpha="1" clip_to_extent="1">
        <layer enabled="1" pass="0" class="SimpleFill" locked="0">
          <prop k="color" v="38,166,91,50"/>
          <prop k="outline_color" v="24,115,67,255"/>
          <prop k="outline_width" v="0.55"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
      <symbol type="fill" name="1" alpha="1" clip_to_extent="1">
        <layer enabled="1" pass="0" class="SimpleFill" locked="0">
          <prop k="color" v="211,47,47,45"/>
          <prop k="outline_color" v="183,28,28,255"/>
          <prop k="outline_style" v="dash"/>
          <prop k="outline_width" v="0.55"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
      <symbol type="fill" name="2" alpha="1" clip_to_extent="1">
        <layer enabled="1" pass="0" class="SimpleFill" locked="0">
          <prop k="color" v="117,117,117,35"/>
          <prop k="outline_color" v="97,97,97,255"/>
          <prop k="outline_width" v="0.45"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <layerGeometryType>2</layerGeometryType>
</qgis>
