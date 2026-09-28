package com.tridium.tagdictionary.tag;

import com.tridium.tagdictionary.condition.BIsTypeCondition;
import niagara.control.BNumericPoint;
import niagara.data.BIDataValue;
import niagara.nre.annotations.Generated;
import niagara.nre.annotations.NiagaraProperty;
import niagara.nre.annotations.NiagaraType;
import niagara.sys.BFacets;
import niagara.sys.BString;
import niagara.sys.Property;
import niagara.sys.Sys;
import niagara.sys.Type;
import niagara.tag.Entity;
import niagara.tag.Tag;
import niagara.tagdictionary.BTagInfo;
import niagara.units.BUnit;

@NiagaraType
@NiagaraProperty(name = "validity", type = "BTagRuleCondition", defaultValue = "new BIsTypeCondition(BNumericPoint.TYPE)", flags = 3, override = true)
public class BQudtUnitTag extends BTagInfo {
   @Generated
   public static final Property validity = newProperty(3, new BIsTypeCondition(BNumericPoint.TYPE), null);// 57
   @Generated
   public static final Type TYPE = Sys.loadType(BQudtUnitTag.class);// 67
   public static final String UNKNOWN_UNIT = "UNKNOWN";

   @Generated
   @Override
   public Type getType() {
      return TYPE;// 65
   }

   @Override
   public Tag getTag(Entity entity) {
      if (entity instanceof BNumericPoint) {// 89
         BNumericPoint np = (BNumericPoint)entity;// 91
         BFacets df = np.getFacets();// 92
         BUnit unit = (BUnit)df.get("units");// 93
         if (unit != null && !unit.isNull()) {// 94
            return new Tag(this.getTagId(), BString.make(unit.getQudtName() != null ? unit.getQudtName() : "UNKNOWN"));// 96
         }
      }

      return null;// 99
   }

   @Override
   public BIDataValue getDefaultValue() {
      return BString.DEFAULT;// 105
   }
}
