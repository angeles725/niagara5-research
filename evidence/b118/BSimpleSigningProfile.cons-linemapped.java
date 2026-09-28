package com.tridium.signing.profile;

import com.tridium.crypto.core.cert.CertUtils;
import com.tridium.crypto.core.cert.KeyPurpose;
import com.tridium.crypto.core.cert.NPKCS10CertificationRequest;
import com.tridium.crypto.core.cert.NSigningParameters;
import com.tridium.crypto.core.cert.NX509Certificate;
import com.tridium.crypto.core.cert.NX509CertificateEntry;
import com.tridium.crypto.core.cert.ext.NBasicConstraints;
import com.tridium.crypto.core.cert.ext.NExtendedKeyUsage;
import com.tridium.crypto.core.cert.ext.NKeyUsage;
import com.tridium.crypto.core.io.CoreCryptoManager;
import com.tridium.platcrypto.signing.BCertificateParameter;
import com.tridium.platcrypto.signing.CertificateParameterType;
import com.tridium.signing.BCertificateSigningRecord;
import com.tridium.signing.SigningServiceException;
import com.tridium.signing.SigningServiceUtils;
import java.security.PrivateKey;
import java.security.UnrecoverableKeyException;
import java.security.cert.X509Certificate;
import java.util.Arrays;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;
import java.util.logging.Level;
import niagara.nre.annotations.Facet;
import niagara.nre.annotations.Generated;
import niagara.nre.annotations.NiagaraProperties;
import niagara.nre.annotations.NiagaraProperty;
import niagara.nre.annotations.NiagaraType;
import niagara.nre.security.CertificateStatusEnum;
import niagara.nre.security.IX509Extension;
import niagara.nre.security.SecretChars;
import niagara.nre.util.SecurityUtil;
import niagara.security.BCertificateAliasAndPassword;
import niagara.security.BCertificateStatusEnum;
import niagara.security.BPassword;
import niagara.security.crypto.CertManagerFactory;
import niagara.security.crypto.ICryptoManager;
import niagara.sys.BBoolean;
import niagara.sys.BFacets;
import niagara.sys.BIReadonlyPropertyContainer;
import niagara.sys.BInteger;
import niagara.sys.BRelTime;
import niagara.sys.BValue;
import niagara.sys.Context;
import niagara.sys.Property;
import niagara.sys.Sys;
import niagara.sys.Type;
import org.bouncycastle.asn1.x509.KeyPurposeId;

@NiagaraType
@NiagaraProperties(
   {
         @NiagaraProperty(name = "caStatus", type = "BCertificateStatusEnum", defaultValue = "BCertificateStatusEnum.ok", flags = 67),
         @NiagaraProperty(
            name = "caAliasAndPassword",
            type = "BCertificateAliasAndPassword",
            defaultValue = "BCertificateAliasAndPassword.DEFAULT",
            facets = @Facet(name = "BFacets.SECURITY", value = "true")
         ),
         @NiagaraProperty(
            name = "expirationPeriod",
            type = "BRelTime",
            defaultValue = "BRelTime.makeDays(365)",
            facets = {
                  @Facet("BFacets.make(BFacets.MIN, BRelTime.makeHours(1))"),
                  @Facet("BFacets.make(BFacets.SHOW_SECONDS, BBoolean.FALSE, \"showDay\", BBoolean.TRUE)"),
                  @Facet(name = "BFacets.SECURITY", value = "true")
            }
         ),
         @NiagaraProperty(
            name = "keyPurpose",
            type = "BKeyPurpose",
            defaultValue = "BKeyPurpose.DEFAULT",
            facets = @Facet(name = "BFacets.SECURITY", value = "true")
         ),
         @NiagaraProperty(
            name = "enforceKeyPurpose",
            type = "boolean",
            defaultValue = "true",
            flags = 4,
            facets = @Facet(name = "BFacets.SECURITY", value = "true")
         ),
         @NiagaraProperty(name = "certificateStore", type = "BSigningRecordStore", defaultValue = "new BSigningRecordStore()")
   }
)
public class BSimpleSigningProfile extends BAbstractSigningProfile implements BIReadonlyPropertyContainer {
   @Generated
   public static final Property caStatus = newProperty(67, BCertificateStatusEnum.ok, null);// 145
   @Generated
   public static final Property caAliasAndPassword = newProperty(0, BCertificateAliasAndPassword.DEFAULT, BFacets.make("security", true));// 173
   @Generated
   public static final Property expirationPeriod = newProperty(
      0,// 199
      BRelTime.makeDays(365),
      BFacets.make(
         BFacets.make(BFacets.make("min", BRelTime.makeHours(1)), BFacets.make("showSeconds", BBoolean.FALSE, "showDay", BBoolean.TRUE)),
         BFacets.make("security", true)
      )
   );
   @Generated
   public static final Property keyPurpose = newProperty(0, BKeyPurpose.DEFAULT, BFacets.make("security", true));// 225
   @Generated
   public static final Property enforceKeyPurpose = newProperty(4, true, BFacets.make("security", true));// 252
   @Generated
   public static final Property certificateStore = newProperty(0, new BSigningRecordStore(), null);// 280
   @Generated
   public static final Type TYPE = Sys.loadType(BSimpleSigningProfile.class);// 304

   @Generated
   public BCertificateStatusEnum getCaStatus() {
      return (BCertificateStatusEnum)this.get(caStatus);// 153
   }

   @Generated
   public void setCaStatus(BCertificateStatusEnum v) {
      this.set(caStatus, v, null);// 161
   }

   @Generated
   public BCertificateAliasAndPassword getCaAliasAndPassword() {
      return (BCertificateAliasAndPassword)this.get(caAliasAndPassword);// 180
   }

   @Generated
   public void setCaAliasAndPassword(BCertificateAliasAndPassword v) {
      this.set(caAliasAndPassword, v, null);// 187
   }

   @Generated
   public BRelTime getExpirationPeriod() {
      return (BRelTime)this.get(expirationPeriod);// 206
   }

   @Generated
   public void setExpirationPeriod(BRelTime v) {
      this.set(expirationPeriod, v, null);// 213
   }

   @Generated
   public BKeyPurpose getKeyPurpose() {
      return (BKeyPurpose)this.get(keyPurpose);// 232
   }

   @Generated
   public void setKeyPurpose(BKeyPurpose v) {
      this.set(keyPurpose, v, null);// 239
   }

   @Generated
   public boolean getEnforceKeyPurpose() {
      return this.getBoolean(enforceKeyPurpose);// 260
   }

   @Generated
   public void setEnforceKeyPurpose(boolean v) {
      this.setBoolean(enforceKeyPurpose, v, null);// 268
   }

   @Generated
   public BSigningRecordStore getCertificateStore() {
      return (BSigningRecordStore)this.get(certificateStore);// 287
   }

   @Generated
   public void setCertificateStore(BSigningRecordStore v) {
      this.set(certificateStore, v, null);// 294
   }

   @Generated
   @Override
   public Type getType() {
      return TYPE;// 302
   }

   @Override
   public final Object fw(int x, Object a, Object b, Object c, Object d) {
      if (x == 11) {// 316
         this.getCaAliasAndPassword().setFacets(BCertificateAliasAndPassword.alias, BFacets.make("purposeId", KeyPurpose.CA_CERT.name()));// 318 320
         this.updateCaStatus();// 323
      } else if (x == 2 && this.isRunning() && caAliasAndPassword.equals(a)) {// 325
         this.updateCaStatus();// 327
      }

      return super.fw(x, a, b, c, d);// 329
   }

   @Override
   protected final BCertificateSigningRecord doRegisterRequester(String requesterId, boolean renewal) throws SigningServiceException {
      Optional<BCertificateSigningRecord> optRec = this.getRecord(requesterId);// 341
      BCertificateSigningRecord record;
      if (optRec.isPresent()) {// 343
         record = optRec.get();// 345
         if (!renewal) {// 346
            BCertificateSigningRecord.resetRecord(record);// 348
         }
      } else {
         record = BCertificateSigningRecord.make(requesterId);// 353
      }

      this.getCertificateStore().store(requesterId, record);// 356
      return record;// 357
   }

   @Override
   protected void doValidateCsr(NPKCS10CertificationRequest csr) throws SigningServiceException {
      BCertificateParameter[] csrParameters = this.getChildren(BCertificateParameter.class);// 364
      SigningServiceUtils.validateKeyType(csr, csrParameters);// 365
      SigningServiceUtils.validateKeySize(csr, csrParameters);// 366
      if (this.getEnforceKeyPurpose()) {// 367
         SigningServiceUtils.checkKeyPurpose(csr, this.getKeyPurpose());// 369
      }

      SigningServiceUtils.validateDn(csr, csrParameters);// 371
      SigningServiceUtils.validateCommonNameTemplate(csr, csrParameters);// 372
   }// 373

   @Override
   protected final X509Certificate doSignCertificate(NPKCS10CertificationRequest csr, String requesterId) throws SigningServiceException {
      if (this.getCaAlias().isEmpty()) {// 379
         throw new SigningServiceException("signingService", "signing.service.ca.alias.notFound");// 381
      } else if ("default".equals(this.getCaAlias())) {// 383
         throw new SigningServiceException("signingService", "signing.service.ca.alias.factory");// 385
      } else {
         NX509CertificateEntry caCert = SecurityUtil.doPrivileged(this::retrieveCaCertificate);// 388

         try {
            NSigningParameters parameters = this.getSigningParameters(csr);// 392
            return CertUtils.signCertificate(csr, caCert, parameters, true).getCertificate();// 393
         } catch (Exception e) {// 395
            String messageLexKey = "signing.service.signing.failed";// 397
            SigningServiceUtils.LOG.log(Level.SEVERE, SigningServiceUtils.LEX.getText(messageLexKey) + e.getMessage(), e);// 398
            throw new SigningServiceException("signingService", messageLexKey, e, e.getMessage());// 399
         }
      }
   }

   private NSigningParameters getSigningParameters(NPKCS10CertificationRequest csr) throws Exception {
      Date notBefore = new Date();// 406
      KeyPurpose keyPurpose = this.getEnforceKeyPurpose() ? this.getKeyPurpose().toKeyPurpose() : null;// 407
      NSigningParameters signingParameters = NSigningParameters.make(// 408
         notBefore, new Date(notBefore.getTime() + this.getExpirationPeriod().getMillis()), keyPurpose// 410
      );

      for (IX509Extension extension : csr.getExtensions()) {// 414
         if (extension instanceof NKeyUsage) {// 416
            if (this.isKeyUsageExtensionValid((NKeyUsage)extension)) {// 418
               signingParameters.addExtension(extension);// 420
            }
         } else if (extension instanceof NExtendedKeyUsage) {// 423
            if (this.isExtendedKeyUsageExtensionValid((NExtendedKeyUsage)extension)) {// 425
               signingParameters.addExtension(extension);// 427
            }
         } else if (extension instanceof NBasicConstraints) {// 430
            if (this.isBasicConstraintsExtensionValid((NBasicConstraints)extension)) {// 432
               signingParameters.addExtension(extension);// 434
            }
         } else {
            signingParameters.addExtension(extension);// 439
         }
      }

      return signingParameters;// 443
   }

   private boolean isKeyUsageExtensionValid(NKeyUsage keyUsageExtension) {
      switch (this.getKeyPurpose().toKeyPurpose()) {// 448
         case SERVER_CERT:
            return CertUtils.checkKeyUsageExtension(keyUsageExtension, 128, 32);// 451
         case CLIENT_CERT:
         case CODE_SIGNING_CERT:
            return CertUtils.checkKeyUsageExtension(keyUsageExtension, 128);// 455
         case CA_CERT:
            return CertUtils.checkKeyUsageExtension(keyUsageExtension, 4, 2);// 458
         default:
            return true;// 461
      }
   }

   private boolean isExtendedKeyUsageExtensionValid(NExtendedKeyUsage extendedKeyUsageExtension) {
      switch (this.getKeyPurpose().toKeyPurpose()) {// 467
         case SERVER_CERT:
            return CertUtils.checkExtendedKeyUsageExtension(extendedKeyUsageExtension, KeyPurposeId.id_kp_serverAuth);// 473
         case CLIENT_CERT:
            return CertUtils.checkExtendedKeyUsageExtension(extendedKeyUsageExtension, KeyPurposeId.id_kp_clientAuth);// 470
         case CODE_SIGNING_CERT:
            return CertUtils.checkExtendedKeyUsageExtension(extendedKeyUsageExtension, KeyPurposeId.id_kp_codeSigning);// 476
         default:
            return true;// 479
      }
   }

   private boolean isBasicConstraintsExtensionValid(NBasicConstraints basicConstraintsExtension) {
      return this.getKeyPurpose().toKeyPurpose() == KeyPurpose.CA_CERT ? CertUtils.checkBasicConstraintsExtension(basicConstraintsExtension) : true;// 485 487 489
   }

   private NX509CertificateEntry retrieveCaCertificate() throws SigningServiceException {
      try {
         String caAlias = this.getCaAlias();// 497
         ICryptoManager cryptoManager = CertManagerFactory.getInstance();// 498
         X509Certificate cert = cryptoManager.getKeyStore().getCertificate(caAlias);// 499
         if (cert == null) {// 500
            throw new SigningServiceException("signingService", "signing.service.ca.notFound", caAlias);// 502
         } else {
            BPassword caPassword = this.getCaAliasAndPassword().getPassword();// 504
            if (caPassword.equals(BPassword.DEFAULT)) {// 505
               throw new SigningServiceException("signingService", "signing.service.ca.pw.notFound");// 507
            } else {
               String password = caPassword.getValue();// 509
               PrivateKey key = (PrivateKey)cryptoManager.getKeyStore().getKey(caAlias, password.toCharArray());// 510
               return NX509CertificateEntry.make(caAlias, new X509Certificate[]{cert}, key);// 511
            }
         }
      } catch (UnrecoverableKeyException e) {// 513
         throw new SigningServiceException(
            "signingService", "signing.service.ca.retrieve.failed", e, SigningServiceUtils.LEX.getText("signing.service.ca.pw.incorrect")// 515 517
         );
      } catch (Exception e) {// 520
         throw new SigningServiceException("signingService", "signing.service.ca.retrieve.failed", e.getMessage(), e);// 522
      }
   }

   @Override
   protected Map<String, BValue> doGetCsrParameters(Context cx) throws SigningServiceException {
      Map<String, BValue> params = new HashMap<>();// 530
      if (this.getEnforceKeyPurpose()) {// 532
         params.put(// 534
            CertificateParameterType.KEY_PURPOSE.name(),// 535
            BCertificateParameter.make(CertificateParameterType.KEY_PURPOSE, BInteger.make(this.getKeyPurpose().getOrdinal()))// 536
         );
      }

      BCertificateParameter[] childParameters = this.getChildren(BCertificateParameter.class);// 539
      Arrays.stream(childParameters).filter(childParam -> {// 541
         return !CertificateParameterType.KEY_PURPOSE.name().equals(childParam.getParameterType());// 542
      }).forEach(childParam -> {
         params.put(childParam.getName(), childParam.getNewInstanceForCsrGeneration(cx));// 543
      });
      return params;// 544
   }

   @Override
   protected final Optional<BCertificateSigningRecord> doGetRecord(String requesterId) throws SigningServiceException {
      return this.getCertificateStore().getRecord(requesterId);// 551
   }

   @Override
   protected final Iterator<BCertificateSigningRecord> doGetAllRecords() throws SigningServiceException {
      return this.getCertificateStore().getAllRecords();// 558
   }

   @Override
   protected final void updateRecord(BCertificateSigningRecord record) throws SigningServiceException {
      this.getCertificateStore().store(record.getRequesterId(), record);// 565
   }// 566

   @Override
   public X509Certificate[] getCaCertificateChain(String requesterId) throws SigningServiceException {
      try {
         String caAlias = this.getCaAlias();// 574
         ICryptoManager cryptoManager = CertManagerFactory.getInstance();// 575
         X509Certificate[] caCertificateChain = cryptoManager.getKeyStore().getCertificateChain(caAlias);// 576
         if (caCertificateChain == null) {// 577
            throw new SigningServiceException("signingService", "signing.service.ca.notFound", caAlias);// 579
         } else {
            return caCertificateChain;// 581
         }
      } catch (SigningServiceException e) {// 583
         throw e;// 585
      } catch (Exception e) {// 587
         throw new SigningServiceException("signingService", "signing.service.ca.retrieve.failed", e.getMessage(), e);// 589
      }
   }

   @Override
   public String getCaFingerprint() throws SigningServiceException {
      try {
         String caAlias = this.getCaAlias();// 599
         ICryptoManager cryptoManager = CertManagerFactory.getInstance();// 600
         X509Certificate caCertificate = cryptoManager.getKeyStore().getCertificate(caAlias);// 601
         if (caCertificate == null) {// 602
            throw new SigningServiceException("signingService", "signing.service.ca.notFound", caAlias);// 604
         } else {
            return NX509Certificate.make(caCertificate).getFingerprint("SHA256");// 606
         }
      } catch (SigningServiceException e) {// 608
         throw e;// 610
      } catch (Exception e) {// 612
         throw new SigningServiceException("signingService", "signing.service.ca.retrieve.failed", e.getMessage(), e);// 614
      }
   }

   private String getCaAlias() {
      return this.getCaAliasAndPassword().getAlias();// 620
   }

   private void updateCaStatus() {
      BCertificateAliasAndPassword aliasAndPassword = this.getCaAliasAndPassword();// 631
      String caAlias = aliasAndPassword.getAlias();// 634
      if (SigningServiceUtils.isDefaultOrEmptyAlias(caAlias)) {// 635
         SecurityUtil.doPrivileged(() -> {// 637
            this.setCaStatus(BCertificateStatusEnum.badKey);// 639
            return null;// 640
         });
      } else {
         BPassword caPassword = aliasAndPassword.getPassword();// 646
         if (BPassword.DEFAULT.equals(caPassword)) {// 647
            SecurityUtil.doPrivileged(() -> {// 649
               this.setCaStatus(BCertificateStatusEnum.badPassword);// 651
               return null;// 652
            });
         } else {
            CertificateStatusEnum certStatus = CertificateStatusEnum.BAD_KEY;// 660

            try {
               CoreCryptoManager ccm = CoreCryptoManager.get();// 663
               certStatus = CertificateStatusEnum.BAD_PASSWORD;// 668
               SecretChars certPasswordChars = SecurityUtil.doPrivileged(caPassword::getSecretChars);// 670 671
               certStatus = ccm.checkCACertificateStatus(caAlias, certPasswordChars);// 672
            } catch (Exception e) {// 674
               if (SigningServiceUtils.LOG.isLoggable(Level.FINE)) {// 676
                  SigningServiceUtils.LOG
                     .log(Level.FINE, "CA Cert validation check failed for profile '" + this.toPathString() + "'. Setting CA Cert Status to " + certStatus, e);// 678 679
               }
            }

            CertificateStatusEnum finalCertStatus = certStatus;// 684
            SecurityUtil.doPrivileged(() -> {// 685
               this.setCaStatus(BCertificateStatusEnum.make(finalCertStatus.ordinal()));// 687
               return null;// 688
            });
         }
      }
   }// 642 654 690
}
