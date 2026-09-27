package poc.n5hello;

import niagara.sys.*;
import niagara.nre.annotations.*;

/**
 * n5-hello PoC (niagara5-research Block 9) — a trivial BComponent with one
 * @NiagaraProperty and one @NiagaraAction, written in the minimal pre-generation
 * form: only the annotations + business-logic stub. Slotomatic + the N5 JSR-269
 * annotation processor are expected to inject the generated slot boilerplate
 * (TYPE field, Property/Action static fields, getters/setters) on build.
 */
@NiagaraType

@NiagaraProperty(
  name = "count",
  type = "int",
  defaultValue = "0"
)

@NiagaraAction(
  name = "increment"
)
public class BN5Hello
  extends BComponent
{
//region /*+ ------------ BEGIN BAJA AUTO GENERATED CODE ------------ +*/
//@formatter:off
/*@ $poc.n5hello.BN5Hello(4228716083)1.0$ @*/
/* Generated Sun Sep 27 05:24:13 CST 2026 by Slot-o-Matic (c) Tridium, Inc. 2012-2026 */

  //region Property "count"

  /**
   * Slot for the {@code count} property.
   * @see #getCount
   * @see #setCount
   */
  public static final Property count = newProperty(0, 0, null);

  /**
   * Get the {@code count} property.
   * @see #count
   */
  public int getCount() { return getInt(count); }

  /**
   * Set the {@code count} property.
   * @see #count
   */
  public void setCount(int v) { setInt(count, v, null); }

  //endregion Property "count"

  //region Action "increment"

  /**
   * Slot for the {@code increment} action.
   * @see #increment()
   */
  public static final Action increment = newAction(0, null);

  /**
   * Invoke the {@code increment} action.
   * @see #increment
   */
  public void increment() { invoke(increment, null, null); }

  //endregion Action "increment"

  //region Type

  @Override
  public Type getType() { return TYPE; }
  public static final Type TYPE = Sys.loadType(BN5Hello.class);

  //endregion Type

//@formatter:on
//endregion /*+ ------------ END BAJA AUTO GENERATED CODE -------------- +*/
  public void doIncrement()
  {
    setCount(getCount() + 1);
  }
}
