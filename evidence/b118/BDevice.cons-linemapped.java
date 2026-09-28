package niagara.driver;

import com.tridium.sys.metrics.BISubLicenseable;
import com.tridium.sys.metrics.Metrics;
import java.util.logging.Logger;
import niagara.alarm.AlarmSupport;
import niagara.alarm.BAlarmRecord;
import niagara.alarm.BAlarmSourceInfo;
import niagara.driver.ping.BIPingable;
import niagara.driver.ping.BPingHealth;
import niagara.driver.ping.BPingMonitor;
import niagara.nre.annotations.Generated;
import niagara.nre.annotations.NiagaraAction;
import niagara.nre.annotations.NiagaraActions;
import niagara.nre.annotations.NiagaraProperties;
import niagara.nre.annotations.NiagaraProperty;
import niagara.nre.annotations.NiagaraType;
import niagara.status.BIStatus;
import niagara.status.BStatus;
import niagara.sys.Action;
import niagara.sys.BBoolean;
import niagara.sys.BComplex;
import niagara.sys.BComponent;
import niagara.sys.BFacets;
import niagara.sys.BIcon;
import niagara.sys.BValue;
import niagara.sys.Context;
import niagara.sys.NotRunningException;
import niagara.sys.Property;
import niagara.sys.Sys;
import niagara.sys.Type;
import niagara.util.BFormat;
import niagara.util.IFuture;

@NiagaraType
@NiagaraProperties(
   {
         @NiagaraProperty(name = "status", type = "BStatus", defaultValue = "BStatus.ok", flags = 75),
         @NiagaraProperty(name = "enabled", type = "boolean", defaultValue = "true"),
         @NiagaraProperty(name = "faultCause", type = "String", defaultValue = "", flags = 67),
         @NiagaraProperty(name = "health", type = "BPingHealth", defaultValue = "new BPingHealth()", flags = 65),
         @NiagaraProperty(name = "alarmSourceInfo", type = "BAlarmSourceInfo", defaultValue = "initAlarmSourceInfo()")
   }
)
@NiagaraActions(
   {
         @NiagaraAction(name = "ping", flags = 16),
         @NiagaraAction(name = "ackAlarm", parameterType = "BAlarmRecord", defaultValue = "new BAlarmRecord()", returnType = "BBoolean", flags = 4)
   }
)
public abstract class BDevice extends BComponent implements BIStatus, BIPingable {
   @Generated
   public static final Property status = newProperty(75, BStatus.ok, null);// 123
   @Generated
   public static final Property enabled = newProperty(0, true, null);// 154
   @Generated
   public static final Property faultCause = newProperty(67, "", null);// 183
   @Generated
   public static final Property health = newProperty(65, new BPingHealth(), null);// 212
   @Generated
   public static final Property alarmSourceInfo = newProperty(0, initAlarmSourceInfo(), null);// 240
   @Generated
   public static final Action ping = newAction(16, (BFacets)null);// 266
   @Generated
   public static final Action ackAlarm = newAction(4, new BAlarmRecord(), null);// 285
   @Generated
   public static final Type TYPE = Sys.loadType(BDevice.class);// 302
   protected static final BIcon icon = BIcon.std("device.png");// 774
   private Logger log;
   private int oldStatus = 0;// 777
   private BDeviceNetwork network;
   private boolean fatalFault;
   private boolean configFault;
   private final AlarmSupport alarmSupport = new AlarmSupport(this, "");// 781

   @Generated
   @Override
   public BStatus getStatus() {
      return (BStatus)this.get(status);// 132
   }

   @Generated
   @Override
   public void setStatus(BStatus v) {
      this.set(status, v, null);// 141
   }

   @Generated
   public boolean getEnabled() {
      return this.getBoolean(enabled);// 162
   }

   @Generated
   public void setEnabled(boolean v) {
      this.setBoolean(enabled, v, null);// 170
   }

   @Generated
   public String getFaultCause() {
      return this.getString(faultCause);// 191
   }

   @Generated
   public void setFaultCause(String v) {
      this.setString(faultCause, v, null);// 199
   }

   @Generated
   @Override
   public BPingHealth getHealth() {
      return (BPingHealth)this.get(health);// 220
   }

   @Generated
   public void setHealth(BPingHealth v) {
      this.set(health, v, null);// 228
   }

   @Generated
   @Override
   public BAlarmSourceInfo getAlarmSourceInfo() {
      return (BAlarmSourceInfo)this.get(alarmSourceInfo);// 247
   }

   @Generated
   public void setAlarmSourceInfo(BAlarmSourceInfo v) {
      this.set(alarmSourceInfo, v, null);// 254
   }

   @Generated
   @Override
   public void ping() {
      this.invoke(ping, null, null);// 274
   }

   @Generated
   @Override
   public BBoolean ackAlarm(BAlarmRecord parameter) {
      return (BBoolean)this.invoke(ackAlarm, parameter, null);// 292
   }

   @Generated
   @Override
   public Type getType() {
      return TYPE;// 300
   }

   public abstract Type getNetworkType();

   public final BDeviceNetwork getNetwork() {
      if (this.network != null) {// 320
         return this.network;// 322
      } else if (!this.isRunning()) {// 324
         throw new NotRunningException();// 326
      } else {
         throw new IllegalStateException(this.getFaultCause());// 328
      }
   }

   public final BDeviceExt[] getDeviceExts() {
      return this.getChildren(BDeviceExt.class);// 338
   }

   public boolean isOperational() {
      return !this.isDisabled() && !this.isDown() && !this.isFault() && !this.isFatalFault();// 350
   }

   public boolean isNonOperational() {
      return !this.isOperational();// 367
   }

   public final boolean isDown() {
      return this.getStatus().isDown();// 380
   }

   public final boolean isDisabled() {
      return this.getStatus().isDisabled();// 390
   }

   public final boolean isFault() {
      return this.getStatus().isFault();// 403
   }

   @Override
   public final void updateStatus() {
      int newStatus = this.getStatus().getBits();// 414
      BStatus network = this.network == null ? BStatus.ok : this.network.getStatus();// 415
      if (this.getEnabled() && !network.isDisabled()) {// 418
         newStatus &= -2;// 424
      } else {
         newStatus |= 1;// 420
      }

      if (!this.getHealth().getDown() && !network.isDown()) {// 428
         newStatus &= -5;// 434
      } else {
         newStatus |= 4;// 430
      }

      if (!this.fatalFault && !this.configFault && !network.isFault()) {// 438
         newStatus &= -3;// 444
      } else {
         newStatus |= 2;// 440
      }

      if (this.oldStatus != newStatus) {// 448
         this.setStatus(BStatus.make(newStatus));// 452
         this.oldStatus = newStatus;// 453
         BDeviceExt[] exts = this.getDeviceExts();// 456

         for (int i = 0; i < exts.length; i++) {// 457
            try {
               exts[i].updateStatus();// 461
            } catch (Throwable e) {// 463
               e.printStackTrace();// 465
            }
         }
      }
   }// 450 468

   public final boolean isFatalFault() {
      return this.fatalFault;// 479
   }

   public final void configOk() {
      this.configFault = false;// 490
      if (!this.fatalFault) {// 493
         this.setFaultCause("");// 499
         this.updateStatus();// 500
      }
   }// 495 501

   public final void configFail(String cause) {
      this.configFault = true;// 511
      if (!this.fatalFault) {// 514
         this.setFaultCause(cause);// 520
         this.updateStatus();// 521
      }
   }// 516 522

   public final void configFatal(String cause) {
      this.fatalFault = true;// 531
      this.setFaultCause(cause);// 532
      this.updateStatus();// 533
   }// 534

   private void checkFatalFault(String badGroups) {
      if (badGroups != null) {// 542
         this.fatalFault = true;// 544
         this.getLogger().severe("Exceeded device limit for " + badGroups);// 545
         this.setFaultCause("Exceeded device limit for " + badGroups);// 546
      } else {
         BDeviceNetwork network = null;// 550
         if (!this.fatalFault) {// 553
            for (BComplex parent = this.getParent(); parent != null; parent = parent.getParent()) {// 559 560 567
               if (parent instanceof BDeviceNetwork) {// 562
                  network = (BDeviceNetwork)parent;// 564
                  break;// 565
               }
            }

            if (network == null) {// 571
               this.fatalFault = true;// 573
               this.setFaultCause("Not under DeviceNetwork");// 574
            } else if (!network.getType().is(this.getNetworkType())) {// 579
               this.fatalFault = true;// 581
               this.setFaultCause("Parent DeviceNetwork " + network.getType() + " is not " + this.getNetworkType());// 582
            } else if (network.isFatalFault()) {// 587
               this.fatalFault = true;// 589
               this.setFaultCause("Network fault: " + network.getFaultCause());// 590
            } else {
               if (this.getType().is(network.getDeviceType())) {// 594
                  Object licenseFault = network.fw(501, BISubLicenseable.getLicenseKey(this, "device.limit"), this, null, null);// 597 599
                  if (licenseFault != null) {// 602
                     this.fatalFault = true;// 604
                     this.setFaultCause(licenseFault.toString());// 605
                     return;// 606
                  }
               }

               this.network = network;// 611
               this.setFaultCause("");// 612
            }
         }
      }
   }// 547 555 575 583 591 613

   protected abstract IFuture postPing();

   @Override
   public abstract void doPing() throws Exception;

   @Override
   public BPingMonitor getMonitor() {
      return this.getNetwork().getMonitor();// 633
   }

   @Override
   public void pingOk() {
      this.getHealth().pingOk();// 644
   }// 645

   @Override
   public void pingFail(String cause) {
      this.getHealth().pingFail(cause);// 654
   }// 655

   @Override
   public BBoolean doAckAlarm(BAlarmRecord ackRequest) {
      return this.getHealth().doAckAlarm(ackRequest);// 664
   }

   @Override
   public IFuture post(Action action, BValue arg, Context cx) {
      if (action.equals(ping)) {// 673
         return this.getStatus().isDisabled() ? null : this.postPing();// 675 677 679
      } else {
         return super.post(action, arg, cx);// 681
      }
   }

   @Override
   public final Object fw(int x, Object a, Object b, Object c, Object d) {
      switch (x) {// 687
         case 2:
            this.fwChanged((Property)a);// 699
            break;// 700
         case 11:
            this.fwStarted();// 690
            break;// 691
         case 13:
            this.fwDescendantsStarted();// 693
            break;// 694
         case 14:
            this.fwDescendantsStopped();// 696
            break;// 697
         case 502:
            return this.alarmSupport;// 702
      }

      return super.fw(x, a, b, c, d);// 704
   }

   private void fwStarted() {
      this.checkFatalFault(Metrics.incrementDevice(this));// 709
   }// 710

   private void fwDescendantsStopped() {
      this.network = null;// 714
   }// 715

   private void fwDescendantsStarted() {
      this.updateStatus();// 719
   }// 720

   private void fwChanged(Property prop) {
      if (this.isRunning()) {// 724
         if (prop == enabled) {// 729
            this.updateStatus();// 731
         }
      }
   }// 726 733

   public Logger getLogger() {
      if (this.log == null) {// 742
         try {
            this.log = Logger.getLogger(this.getNetwork().getLogger().getName() + "." + this.getName());// 746
         } catch (Exception e) {// 748
            this.log = Logger.getLogger(this.getType().getTypeName());// 750
         }
      }

      return this.log;// 753
   }

   static BAlarmSourceInfo initAlarmSourceInfo() {
      BAlarmSourceInfo asi = new BAlarmSourceInfo();// 758
      asi.setSourceName(BFormat.make("%parent.parent.displayName% %parent.displayName%"));// 759
      asi.setToOffnormalText(BFormat.make("%lexicon(driver:pingFail)%"));// 760
      asi.setToNormalText(BFormat.make("%lexicon(driver:pingSuccess)%"));// 761
      return asi;// 762
   }

   @Override
   public BIcon getIcon() {
      return icon;// 771
   }
}
