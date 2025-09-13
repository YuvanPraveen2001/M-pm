-- Table: EmpFundingSourceExclusionAudit
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpFundingSourceExclusionAudit (
	EmpFundingSourceExclusionId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	FundingSourceID int NOT NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL
);

-- Table: EmployeeAvailabilityDateTime
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeAvailabilityDateTime (
	EmployeeAvailabilityDateTimeId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	WeekDay int NULL,
	AvailableFrom time NULL,
	AvailableTo time NULL,
	AvailabilityDateFrom datetime NULL,
	AvailabilityDateTo datetime NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	EmployeeAvailabilityTitleId int NULL,
	AvailabilityStatusId int DEFAULT 2 NOT NULL,
	AvailabilityTypesId int NULL,
	AvailabilityReason varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ApprovalDate datetime NULL,
	TotalDesiredHourPerWeek decimal(18,2) NULL,
	CONSTRAINT PK__ManageEm__8BBD0015A95C8E26 PRIMARY KEY (EmployeeAvailabilityDateTimeId)
);

-- Table: Appointment
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Appointment (
	AppointmentId int IDENTITY(1,1) NOT NULL,
	PatientId int NOT NULL,
	AuthId int NOT NULL,
	AuthDetailId int NOT NULL,
	ServiceTypeId int NOT NULL,
	ServiceSubTypeId int NULL,
	EmployeeId int NOT NULL,
	ScheduledDate datetime NOT NULL,
	ScheduledMinutes int NOT NULL,
	AppointmentStatusId int NOT NULL,
	LocationId int NOT NULL,
	Miles decimal(10,2) NULL,
	HasPayroll bit NOT NULL,
	HasBilling bit NOT NULL,
	Notes nvarchar(4000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsBillable bit NOT NULL,
	IsInternalAppointment bit NOT NULL,
	IsNonPayable bit NOT NULL,
	GroupMasterId int NULL,
	GroupAppointment char(1) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Createdate datetime NOT NULL,
	Createdby int NOT NULL,
	Updatedate datetime NULL,
	Updatedby int NULL,
	IsMigrated bit DEFAULT 0 NULL,
	RenderedDate datetime NULL,
	RenderedMinutes int NULL,
	RenderedBy int NULL,
	RenderedDoneDateTime datetime NULL,
	Breaks decimal(10,2) NULL,
	AppointmentStatusCategoryId int DEFAULT 0 NULL,
	EarningCodeId int NULL,
	AppointmentRuleIds varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	copaybilled int DEFAULT 1 NULL,
	IgnoreRules bit DEFAULT 0 NULL,
	ASiteId int NULL,
	CreatedDeviceBy varchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UpdatedDeviceBy varchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsMakeUp bit DEFAULT 0 NOT NULL,
	DCPatientId int NULL,
	RenderedMediumId int NULL,
	MakeupDate datetime NULL,
	IsFillIn bit DEFAULT 0 NOT NULL,
	DisplacementId int NULL,
	ScheduledDateOnly date NULL,
	RenderedDateOnly date NULL,
	RenderedStartTimeUTC datetime NULL,
	RenderedEndTimeUTC datetime NULL,
	RenderedDoneTimeUTC datetime NULL,
	ScheduledDateUTC date NULL,
	ScheduledStartDateTimeUTC datetime NULL,
	ScheduledEndDateTimeUTC datetime NULL,
	DriveTime decimal(10,2) NULL,
	Mileage decimal(10,2) NULL,
	LunchTimeMinutes int NULL,
	IsDriveTime bit DEFAULT 0 NOT NULL,
	AppointmentDriveTimeLogId int NULL,
	MotivitySyncStatus varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Appointm__8ECDFCC2AEAC1FC6 PRIMARY KEY (AppointmentId),
    CONSTRAINT FK__Appointme__Appoi__5B2E79DB FOREIGN KEY (AppointmentStatusId) REFERENCES AIStagingDB_20250811.dbo.AppointmentStatus(AppointmentStatusId),
    CONSTRAINT FK__Appointme__AuthD__575DE8F7 FOREIGN KEY (AuthDetailId) REFERENCES AIStagingDB_20250811.dbo.AuthDetail(AuthDetailId),
    CONSTRAINT FK__Appointme__AuthI__5669C4BE FOREIGN KEY (AuthId) REFERENCES AIStagingDB_20250811.dbo.Auth(AuthId),
    CONSTRAINT FK__Appointme__Emplo__5A3A55A2 FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__Appointme__Locat__5C229E14 FOREIGN KEY (LocationId) REFERENCES AIStagingDB_20250811.dbo.Location(LocationId),
    CONSTRAINT FK__Appointme__Patie__53385258 FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId),
    CONSTRAINT FK__Appointme__Servi__58520D30 FOREIGN KEY (ServiceTypeId) REFERENCES AIStagingDB_20250811.dbo.ServiceType(ServiceTypeId),
    CONSTRAINT FK__Appointme__Servi__59463169 FOREIGN KEY (ServiceSubTypeId) REFERENCES AIStagingDB_20250811.dbo.SeviceSubType(ServiceSubTypeId)
);

-- Table: Auth
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Auth (
	AuthId int IDENTITY(1,1) NOT NULL,
	OnsetDate date NULL,
	Description nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReferringPhysicianTitle varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReferringPhysicianName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReferringPhysicianNPI varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Diagnosis1 varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Diagnosis2 varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Diagnosis3 varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Diagnosis4 varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Notes varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TreatmentTypeId int NOT NULL,
	FundingSourceID int NOT NULL,
	PayorNumber varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AuthNumber varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StartDate datetime NULL,
	EndDate datetime NULL,
	AuthType int NULL,
	CoPay decimal(10,2) NULL,
	Deductible decimal(10,2) NULL,
	SupervisorId int NOT NULL,
	IsPlaceHolder bit NOT NULL,
	TotalAuthId int NULL,
	UploadAuth varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Value varchar(150) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	InsuranceId varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	PatientId int NOT NULL,
	DocId int NULL,
	IsValidateVisitAgainstAuth bit NULL,
	Valid bit NULL,
	CMS4 nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CMS11 nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SupervisorName nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AuthStatusId int NULL,
	CommittedhoursPerWeek int NULL,
	ExtrenalPatientId int NULL,
	StopBilling bit NULL,
	COInsurance varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	OOPM decimal(18,2) NULL,
	MRNNumber varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SupervisorTwoId int NULL,
	IsFeedingAuth bit DEFAULT 0 NOT NULL,
	Box11c varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsSignatureRequiredinBox13 bit DEFAULT 1 NULL,
	ActingSupervisor int NULL,
	ClientApprovedHours decimal(10,2) NULL,
	DisplacementNumber int NULL,
	DisplacementRate decimal(10,2) NULL,
	ReferralDate date NULL,
	Idqualifier17a varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CaseManagerId int NULL,
	AuthSubmittedDate datetime NULL,
	UseInsuredBillingId int NULL,
	ReferringPhysicianMiddleName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReferringPhysicianLastName nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Auth__C2E32258524A0423 PRIMARY KEY (AuthId),
    CONSTRAINT FK_Auth_AuthStatus FOREIGN KEY (AuthStatusId) REFERENCES AIStagingDB_20250811.dbo.AuthStatus(AuthStatusID),
    CONSTRAINT FK_FundingSourceAuth FOREIGN KEY (FundingSourceID) REFERENCES AIStagingDB_20250811.dbo.FundingSource(FundingSourceID),
    CONSTRAINT FK_TreatmentType_Auth FOREIGN KEY (TreatmentTypeId) REFERENCES AIStagingDB_20250811.dbo.TreatmentType(TreatmentTypeid),
    CONSTRAINT FK__Auth__PatientId__73A521EA FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId)
);

-- Table: AuthDetail
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.AuthDetail (
	AuthDetailId int IDENTITY(1,1) NOT NULL,
	AuthId int NOT NULL,
	ServiceTypeId int NULL,
	ServiceSubTypeId int NULL,
	StartDate datetime NULL,
	EndDate datetime NULL,
	RatePer int NULL,
	UnitsinMins int NULL,
	BillingRate decimal(10,2) NULL,
	CptServiceCodeId int NULL,
	AuthDetailNotes varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Mod1 int NULL,
	Mod2 int NULL,
	Mod3 int NULL,
	Mod4 int NULL,
	AuthDetailAuthNumber varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MaxBy int NULL,
	MaxByFrequency int NULL,
	MaxByValue decimal(10,2) NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CommittedhoursPerWeek decimal(18,2) NULL,
	SplitTypeId int NULL,
	DegreeLabelId int NULL,
	BillRateId int NULL,
	MaxByValueinHour decimal(10,2) NULL,
	SchedulingPercentage decimal(18,2) DEFAULT 100 NOT NULL,
	IsCombinedAuth bit DEFAULT 0 NOT NULL,
	DiscountPercentage decimal(10,4) NULL,
	CONSTRAINT PK__AuthDeta__9406759CF8AB17C3 PRIMARY KEY (AuthDetailId),
    CONSTRAINT FK_Auth_AuthDetail FOREIGN KEY (AuthId) REFERENCES AIStagingDB_20250811.dbo.Auth(AuthId),
    CONSTRAINT FK__AuthDetai__Split__73E5190C FOREIGN KEY (SplitTypeId) REFERENCES AIStagingDB_20250811.dbo.SplitType(SplitTypeId)
);

-- Table: EmpClearance
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpClearance (
	EmpClearanceId int IDENTITY(1,1) NOT NULL,
	EmployeeID int NOT NULL,
	EmpClearanceTypeId int NOT NULL,
	IssueDate date NULL,
	Expirationdate date NULL,
	DocId int NULL,
	NotRequired bit DEFAULT 0 NOT NULL,
	Active bit DEFAULT 1 NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsReadClearance bit DEFAULT 0 NOT NULL,
	IsReadClearanceHrSupervisor bit DEFAULT 0 NOT NULL,
	MarkInactiveIfExpired bit DEFAULT 1 NULL,
	CONSTRAINT PK__EmpClear__46EA12EC4966374A PRIMARY KEY (EmpClearanceId),
    CONSTRAINT FK__EmpCleara__Emplo__673F4B05 FOREIGN KEY (EmployeeID) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId)
);

-- Table: EmpClearanceType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpClearanceType (
	EmpClearanceTypeId int IDENTITY(1,1) NOT NULL,
	EmployeeTypeId int NOT NULL,
	Name nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpClear__6C410B728C1811A1 PRIMARY KEY (EmpClearanceTypeId),
    CONSTRAINT FK_EmpClearanceType_EmployeeTypeId FOREIGN KEY (EmployeeTypeId) REFERENCES AIStagingDB_20250811.dbo.EmployeeType(EmployeeTypeId)
);

-- Table: EmpClearanceTypeSiteMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpClearanceTypeSiteMapping (
	EmpClearanceTypeSiteMappingId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	EmpClearanceTypeId int NOT NULL,
	Active bit NOT NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpClear__FB29C23D2E73B4AA PRIMARY KEY (EmpClearanceTypeSiteMappingId),
    CONSTRAINT FK__EmpCleara__EmpCl__636EBA21 FOREIGN KEY (EmpClearanceTypeId) REFERENCES AIStagingDB_20250811.dbo.EmpClearanceType(EmpClearanceTypeId),
    CONSTRAINT FK__EmpCleara__SiteI__627A95E8 FOREIGN KEY (SiteId) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId)
);

-- Table: EmpCredential
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpCredential (
	EmpCredentialId int IDENTITY(1,1) NOT NULL,
	EmployeeID int NOT NULL,
	EmpCredentialTypeId int NOT NULL,
	IssueDate date NULL,
	Expirationdate date NULL,
	DocId int NULL,
	NotRequired bit DEFAULT 0 NOT NULL,
	Active bit DEFAULT 1 NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsReadCredential bit DEFAULT 0 NOT NULL,
	IsReadCredentialHrSupervisor bit DEFAULT 0 NOT NULL,
	CredentialDocumentNo nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MarkInactiveIfExpired bit DEFAULT 1 NULL,
	CONSTRAINT PK__EmpCrede__456113999882A950 PRIMARY KEY (EmpCredentialId),
    CONSTRAINT FK__EmpCreden__Emplo__57FD0775 FOREIGN KEY (EmployeeID) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId)
);

-- Table: EmpCredentialType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpCredentialType (
	EmpCredentialTypeId int IDENTITY(1,1) NOT NULL,
	EmployeeTypeId int NOT NULL,
	Name nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpCrede__374A5A57758D8423 PRIMARY KEY (EmpCredentialTypeId),
    CONSTRAINT FK_EmpCredentialType_EmployeeTypeId FOREIGN KEY (EmployeeTypeId) REFERENCES AIStagingDB_20250811.dbo.EmployeeType(EmployeeTypeId)
);

-- Table: EmpCredentialTypeSiteMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpCredentialTypeSiteMapping (
	EmpCredentialTypeSiteMappingId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	EmpCredentialTypeId int NOT NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpCrede__A9D9399E6214F03F PRIMARY KEY (EmpCredentialTypeSiteMappingId),
    CONSTRAINT FK__EmpCreden__EmpCr__2077C861 FOREIGN KEY (EmpCredentialTypeId) REFERENCES AIStagingDB_20250811.dbo.EmpCredentialType(EmpCredentialTypeId),
    CONSTRAINT FK__EmpCreden__SiteI__1F83A428 FOREIGN KEY (SiteId) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId)
);

-- Table: EmpFundingSourceExclusion
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpFundingSourceExclusion (
	EmpFundingSourceExclusionId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	FundingSourceID int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpFundi__F489522DA90F6DB8 PRIMARY KEY (EmpFundingSourceExclusionId),
    CONSTRAINT FK__EmpFundin__Emplo__1229A90A FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmpFundin__Fundi__131DCD43 FOREIGN KEY (FundingSourceID) REFERENCES AIStagingDB_20250811.dbo.FundingSource(FundingSourceID)
);

-- Table: EmpPatientExclusion
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpPatientExclusion (
	EmpPatientExclusionId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	PatientId int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpPatie__90B7E0DD5A643B7F PRIMARY KEY (EmpPatientExclusionId),
    CONSTRAINT FK__EmpPatien__Emplo__7C3A67EB FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmpPatien__Patie__2A01329B FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId)
);

-- Table: EmpQualification
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpQualification (
	EmpQualificationId int IDENTITY(1,1) NOT NULL,
	EmployeeID int NOT NULL,
	EmpQualificationTypeId int NOT NULL,
	IssueDate date NULL,
	Expirationdate date NULL,
	DocId int NULL,
	NotRequired bit DEFAULT 0 NOT NULL,
	Active bit DEFAULT 1 NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsReadQualification bit DEFAULT 0 NOT NULL,
	IsReadQualificationHrSupervisor bit DEFAULT 0 NOT NULL,
	MarkInactiveIfExpired bit DEFAULT 1 NULL,
	CONSTRAINT PK__EmpQuali__E3D66C77BA1FF3E0 PRIMARY KEY (EmpQualificationId),
    CONSTRAINT FK__EmpQualif__Emplo__758D6A5C FOREIGN KEY (EmployeeID) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId)
);

-- Table: EmpQualificationType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpQualificationType (
	EmpQualificationTypeId int IDENTITY(1,1) NOT NULL,
	EmployeeTypeId int NOT NULL,
	Name nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpQuali__4B8F2ED06606323D PRIMARY KEY (EmpQualificationTypeId),
    CONSTRAINT FK__EmpQualif__Emplo__216BEC9A FOREIGN KEY (EmployeeTypeId) REFERENCES AIStagingDB_20250811.dbo.EmployeeType(EmployeeTypeId)
);

-- Table: EmpQualificationTypeSiteMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpQualificationTypeSiteMapping (
	EmpQualificationTypeSiteMappingId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	EmpQualificationTypeId int NOT NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpQuali__9C3AAE6C093D7EBB PRIMARY KEY (EmpQualificationTypeSiteMappingId),
    CONSTRAINT FK__EmpQualif__EmpQu__71BCD978 FOREIGN KEY (EmpQualificationTypeId) REFERENCES AIStagingDB_20250811.dbo.EmpQualificationType(EmpQualificationTypeId),
    CONSTRAINT FK__EmpQualif__SiteI__70C8B53F FOREIGN KEY (SiteId) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId)
);

-- Table: EmpTraining
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpTraining (
	EmpTrainingId int IDENTITY(1,1) NOT NULL,
	EmployeeID int NOT NULL,
	EmpTrainingTypeId int NOT NULL,
	IssueDate date NULL,
	Expirationdate date NULL,
	DocId int NULL,
	NotRequired bit DEFAULT 0 NOT NULL,
	Active bit DEFAULT 1 NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsReadTraining bit DEFAULT 0 NOT NULL,
	IsReadTrainingHrSupervisor bit DEFAULT 0 NOT NULL,
	MarkInactiveIfExpired bit DEFAULT 1 NULL,
	CONSTRAINT PK__EmpTrain__456113999882A950 PRIMARY KEY (EmpTrainingId),
    CONSTRAINT FK__EmpTrain__Emplo__57FD0775 FOREIGN KEY (EmployeeID) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId)
);

-- Table: EmpTrainingType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpTrainingType (
	EmpTrainingTypeId int IDENTITY(1,1) NOT NULL,
	EmployeeTypeId int NOT NULL,
	Name nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpTrain__2A406143FE44998D PRIMARY KEY (EmpTrainingTypeId),
    CONSTRAINT FK_EmpTrainingType_EmployeeTypeId FOREIGN KEY (EmployeeTypeId) REFERENCES AIStagingDB_20250811.dbo.EmployeeType(EmployeeTypeId)
);

-- Table: EmpTrainingTypeSiteMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmpTrainingTypeSiteMapping (
	EmpTrainingTypeSiteMappingId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	EmpTrainingTypeId int NOT NULL,
	Active bit NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__EmpTrain__1BDB136DAB704757 PRIMARY KEY (EmpTrainingTypeSiteMappingId),
    CONSTRAINT FK__EmpTraining__EmpCr__2077C861 FOREIGN KEY (EmpTrainingTypeId) REFERENCES AIStagingDB_20250811.dbo.EmpTrainingType(EmpTrainingTypeId),
    CONSTRAINT FK__EmpTraining__SiteI__1F83A428 FOREIGN KEY (SiteId) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId)
);

-- Table: Employee
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Employee (
	EmployeeId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	TreatmentTypeId int NULL,
	LastName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	FirstName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MiddleName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Prefix varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Suffix varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PhoneOffice varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PhoneCell varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	NickName varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DateOfBirth datetime NULL,
	Gender int NULL,
	SSN varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DriverLicenceNumber varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LicenceExpirationDate datetime NULL,
	HiringDate datetime NULL,
	CredentialTypeId int NULL,
	TerminationDate datetime NULL,
	Email varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdditionalNotes varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ServiceAreaZip varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	[Language] int NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsSupervisor bit DEFAULT 0 NOT NULL,
	ExternalSoftwareId varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsStaffMilitaryService bit DEFAULT 0 NOT NULL,
	IsTherpistBillablePrivate bit DEFAULT 0 NOT NULL,
	Title varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	NPI varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CASHId int NULL,
	ZoneId int NULL,
	Active bit DEFAULT 1 NOT NULL,
	IsEligibleForPaidTimeOff bit DEFAULT 0 NOT NULL,
	IsExemptStaff bit DEFAULT 0 NOT NULL,
	IsGetsPaidHoliday bit DEFAULT 0 NOT NULL,
	MaxHoursForDay int NULL,
	MaxHoursForWeek int NULL,
	ADPEmployeeId nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TaxonomyCode varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	HighestDegree varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DegreeLabelId int NULL,
	IsPartTime bit NULL,
	IsContractor bit NULL,
	ImageId int NULL,
	SignatureValidFrom datetime NULL,
	SignatureValidTo datetime NULL,
	EmployeeContactId int NULL,
	EmployeeEmergencyContactId int NULL,
	EmployeeTypeId int NULL,
	DocId int NULL,
	Color nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsPasswordChanged bit DEFAULT 0 NULL,
	SupervisorId int NULL,
	IsInternalStaff bit NULL,
	IsFirebaseCreate bit DEFAULT 0 NULL,
	HrId int NULL,
	Suspended bit DEFAULT 0 NOT NULL,
	IsSms bit DEFAULT 0 NOT NULL,
	EmployeeWorkTypeId int NULL,
	PayTypeId int NULL,
	OnBoardingStatusId int NULL,
	CertificationNumber varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StateLicence varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PreferredPronoun varchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	UseSupervisorsNPI bit DEFAULT 0 NOT NULL,
	Alias varchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MotivitySyncStatus varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Credentials varchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Employee__AF4CE86509BBB543 PRIMARY KEY (EmployeeId),
    CONSTRAINT FK_Employee_CredentialTypeId FOREIGN KEY (CredentialTypeId) REFERENCES AIStagingDB_20250811.dbo.CredentialType(CredentialTypeId),
    CONSTRAINT FK_Employee_Employee_Gender FOREIGN KEY (Gender) REFERENCES AIStagingDB_20250811.dbo.Gender(GenderID),
    CONSTRAINT FK_Employee_TreatmentTypeId FOREIGN KEY (TreatmentTypeId) REFERENCES AIStagingDB_20250811.dbo.TreatmentType(TreatmentTypeid),
    CONSTRAINT FK__Employee__Employ__2FBA0BF1 FOREIGN KEY (EmployeeContactId) REFERENCES AIStagingDB_20250811.dbo.Location(LocationId),
    CONSTRAINT FK__Employee__Employ__30AE302A FOREIGN KEY (EmployeeEmergencyContactId) REFERENCES AIStagingDB_20250811.dbo.Location(LocationId),
    CONSTRAINT FK__Employee__SiteId__6F1576F7 FOREIGN KEY (SiteId) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId),
    CONSTRAINT FK__Employee__ZoneId__6A50C1DA FOREIGN KEY (ZoneId) REFERENCES AIStagingDB_20250811.dbo.[Zone](ZoneId)
);

-- Table: EmployeeLanguageMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeLanguageMapping (
	EmployeeLanguageMappingId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	LanguageID int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_EmployeeLanguageMapping PRIMARY KEY (EmployeeLanguageMappingId),
    CONSTRAINT FK_EmployeeLanguageMapping_Employee FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK_EmployeeLanguageMapping_LanguagePreferred FOREIGN KEY (LanguageID) REFERENCES AIStagingDB_20250811.dbo.LanguagePreferred(LanguageID)
);

-- Table: EmployeeLeave
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeLeave (
	EmployeeLeaveId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	LeaveDate date NOT NULL,
	StartTime time NULL,
	EndTime time NULL,
	StartDate date NULL,
	EndDate date NULL,
	NoOfhours decimal(18,2) NULL,
	NoOfDays int NULL,
	LeaveStatusId int NOT NULL,
	Notes nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LeaveTypeId int NOT NULL,
	ApprovedByEmployeeId int NULL,
	DateApproved datetime NULL,
	ApproverNotes nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	FilePath varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT NULL NULL,
	Filename varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT NULL NULL,
	DocumentId int DEFAULT NULL NULL,
	CONSTRAINT PK__Employee__56D0D486AF89095A PRIMARY KEY (EmployeeLeaveId),
    CONSTRAINT FK__EmployeeL__Appro__18D6A699 FOREIGN KEY (ApprovedByEmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmployeeL__Emplo__15FA39EE FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmployeeL__Leave__16EE5E27 FOREIGN KEY (LeaveStatusId) REFERENCES AIStagingDB_20250811.dbo.LeaveStatus(LeaveStatusId),
    CONSTRAINT FK_employeeleaveLeaveTypeId FOREIGN KEY (LeaveTypeId) REFERENCES AIStagingDB_20250811.dbo.EmployeeLeaveType(LeaveTypeId)
);

-- Table: EmployeeLeaveType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeLeaveType (
	LeaveTypeId int IDENTITY(1,1) NOT NULL,
	Name varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	SiteId int NULL,
	Active bit DEFAULT 1 NOT NULL,
	CONSTRAINT PK__Employee__43BE8F1469ABE7D6 PRIMARY KEY (LeaveTypeId)
);

-- Table: EmployeeType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeType (
	EmployeeTypeId int IDENTITY(1,1) NOT NULL,
	EmployeeTypeName nvarchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_EmployeeType PRIMARY KEY (EmployeeTypeId)
);

-- Table: Gender
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Gender (
	GenderID int IDENTITY(1,1) NOT NULL,
	GenderType varchar(55) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime DEFAULT getdate() NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__Gender__4E24E8177AE99AC3 PRIMARY KEY (GenderID)
);

-- Table: LeaveStatus
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.LeaveStatus (
	LeaveStatusId int IDENTITY(1,1) NOT NULL,
	Name varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__LeaveSta__75EE81FA8480E5E9 PRIMARY KEY (LeaveStatusId)
);

-- Table: Patient
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Patient (
	PatientId int IDENTITY(1,1) NOT NULL,
	SiteId int NOT NULL,
	LastName nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	FirstName nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MiddleName nvarchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Prefix nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Suffix nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ActiveFrom date NULL,
	ActiveTo date NULL,
	DOB date NULL,
	Gender int NULL,
	Email varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdditionalEmail varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AdditionalNotes varchar(3000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	StatusId int NULL,
	ImageFileUrl varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsActive bit NULL,
	DoNotSendSms bit NULL,
	ExternalSoftwareId varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DocId int NULL,
	IsPasswordChanged bit DEFAULT 0 NULL,
	IsInternalClient bit NULL,
	ExtrenalPatientId int NULL,
	ExtrenalSiteId int NULL,
	ExternalSoftwareSiteId int NULL,
	Color nvarchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	EnableClientSMS bit DEFAULT 1 NULL,
	WalletId varchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsSoapNoteDownload bit DEFAULT 0 NOT NULL,
	IsVBMAPPEnabled bit DEFAULT 0 NOT NULL,
	MotivitySyncStatus varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Patient__0F77C6A902835D0A PRIMARY KEY (PatientId)
);

-- Table: PatientLocationMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.PatientLocationMapping (
	PatientLocationMappingId int IDENTITY(1,1) NOT NULL,
	PatientId int NOT NULL,
	LocationId int NOT NULL,
	Active bit NULL,
	CreateDate datetime NULL,
	CreatedBy int NULL,
	IsDefault bit DEFAULT 0 NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_PatientLocationMapping PRIMARY KEY (PatientLocationMappingId)
);

-- Table: TreatmentType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.TreatmentType (
	TreatmentTypeid int IDENTITY(1,1) NOT NULL,
	TreatmentTypeDesc varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	CreateDate datetime NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsMaster bit DEFAULT 0 NULL,
	CONSTRAINT PK__Treatmen__F3EEEAA12AA6CE0A PRIMARY KEY (TreatmentTypeid)
);

-- Table: TreatmentTypeSiteMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.TreatmentTypeSiteMapping (
	TreatmentTypeSiteMappingId int IDENTITY(1,1) NOT NULL,
	TreatmentTypeId int NULL,
	SiteId int NULL,
	IsActive bit DEFAULT 0 NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__Treatmen__D25A43D240D5F1E6 PRIMARY KEY (TreatmentTypeSiteMappingId)
);

-- Table: Zone
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.[Zone] (
	ZoneId int IDENTITY(1,1) NOT NULL,
	ZoneName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ZoneType int NOT NULL,
	SiteId int NOT NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	SiteMainZone bit DEFAULT 0 NOT NULL,
	TimeZoneId varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TimeZoneUtcOffset varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ZoneInternalId varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsFLSARuleorCARule bit DEFAULT 1 NOT NULL,
	IsEVVEnable bit DEFAULT 0 NOT NULL,
	IsLatLongEnabled bit DEFAULT 0 NOT NULL,
	PaymentPublicAPIKey varchar(2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PaymentPrivateAPIKey varchar(2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__Zone__601667B562A7F400 PRIMARY KEY (ZoneId)
);

-- Table: PatientZoneMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.PatientZoneMapping (
	PatientZoneMappingId int IDENTITY(1,1) NOT NULL,
	PatientId int NOT NULL,
	ZoneId int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_PatientZoneMapping PRIMARY KEY (PatientZoneMappingId),
	CONSTRAINT FK__PatientZo__Patie__57C7FD4B FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId),
	CONSTRAINT FK__PatientZo__ZoneI__772B9A0B FOREIGN KEY (ZoneId) REFERENCES AIStagingDB_20250811.dbo.[Zone](ZoneId)
);

-- Table: EmployeeServiceRate
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeServiceRate (
	EmployeeServiceRateId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	ServiceTypeId int NOT NULL,
	Rate decimal(18,2) NOT NULL,
	MileageRate decimal(18,2) NULL,
	Active bit NOT NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__Employee__C6C8FCE9DB539AEA PRIMARY KEY (EmployeeServiceRateId),
    CONSTRAINT FK__EmployeeS__Emplo__3726238F FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmployeeS__Servi__381A47C8 FOREIGN KEY (ServiceTypeId) REFERENCES AIStagingDB_20250811.dbo.ServiceType(ServiceTypeId)
);

-- Table: EmployeeTreatmentTypeMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeTreatmentTypeMapping (
	EmployeeTreatmentTypeMappingId int IDENTITY(1,1) NOT NULL,
	TreatmentTypeId int NOT NULL,
	EmployeeId int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_EmployeeTreatmentTypeMapping PRIMARY KEY (EmployeeTreatmentTypeMappingId),
    CONSTRAINT FK_EmployeeTreatmentTypeMapping_Employee FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK_EmployeeTreatmentTypeMapping_TreatmentType FOREIGN KEY (TreatmentTypeId) REFERENCES AIStagingDB_20250811.dbo.TreatmentType(TreatmentTypeid)
);

-- Table: EmployeeZoneMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.EmployeeZoneMapping (
	EmployeeZoneMappingId int IDENTITY(1,1) NOT NULL,
	EmployeeId int NOT NULL,
	ZoneId int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_EmployeeZoneMapping PRIMARY KEY (EmployeeZoneMappingId),
    CONSTRAINT FK__EmployeeZ__Emplo__7913E27D FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__EmployeeZ__ZoneI__7A0806B6 FOREIGN KEY (ZoneId) REFERENCES AIStagingDB_20250811.dbo.[Zone](ZoneId)
);

-- Table: Location
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Location (
	LocationId int IDENTITY(1,1) NOT NULL,
	Name varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Address1 varchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	Address2 nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Address3 nvarchar(255) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	City varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StateId int NULL,
	ZipCode varchar(10) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Phone varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	AltPhone varchar(15) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsDefaultLocation bit NULL,
	PlaceOfServiceId int DEFAULT 1 NOT NULL,
	Active bit NULL,
	Notes varchar(3000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	DoNotUseFromDriveTime bit DEFAULT 0 NOT NULL,
	IsUseProviderAddress bit DEFAULT 0 NOT NULL,
	CountryCodeId int NULL,
	TaxonomyOverride33b nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Override32aNPI nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Override33aNPI nvarchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Longitude decimal(18,10) NULL,
	Latitude decimal(18,10) NULL,
	CONSTRAINT PK__Location__79309323C5A644D0 PRIMARY KEY (LocationId),
    CONSTRAINT FK_CountryCodeId FOREIGN KEY (CountryCodeId) REFERENCES AIStagingDB_20250811.dbo.CountryCode(CountryCodeId),
    CONSTRAINT FK__Location__PlaceO__5E1FF51F FOREIGN KEY (PlaceOfServiceId) REFERENCES AIStagingDB_20250811.dbo.PlaceOfService(PlaceOfServiceId),
    CONSTRAINT FK__Location__StateI__489AC854 FOREIGN KEY (StateId) REFERENCES AIStagingDB_20250811.dbo.State(StateId)
);

-- Table: PatientEmployeeTeam
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.PatientEmployeeTeam (
	PatientEmployeeTeamId int IDENTITY(1,1) NOT NULL,
	PatientId int NOT NULL,
	EmployeeId int NOT NULL,
	TeamLevelId int NOT NULL,
	CreateDate datetime NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	ValidFrom datetime NULL,
	ValidTo datetime NULL,
	TreatmentTypeId int NULL,
	Notes nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CONSTRAINT PK__PatientE__75F044154B6209D2 PRIMARY KEY (PatientEmployeeTeamId),
    CONSTRAINT FK__PatientEm__Emplo__733B0D96 FOREIGN KEY (EmployeeId) REFERENCES AIStagingDB_20250811.dbo.Employee(EmployeeId),
    CONSTRAINT FK__PatientEm__Patie__4D4A6ED8 FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId)
);

-- Table: PatientLanguageMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.PatientLanguageMapping (
	PatientLanguageMappingId int IDENTITY(1,1) NOT NULL,
	PatientId int NOT NULL,
	LanguageID int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK_PatientLanguageMapping PRIMARY KEY (PatientLanguageMappingId),
    CONSTRAINT FK_PatientLanguageMapping_LanguagePreferred FOREIGN KEY (LanguageID) REFERENCES AIStagingDB_20250811.dbo.LanguagePreferred(LanguageID),
    CONSTRAINT FK__PatientLa__Patie__5026DB83 FOREIGN KEY (PatientId) REFERENCES AIStagingDB_20250811.dbo.Patient(PatientId)
);

-- Table: ServiceType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.ServiceType (
	ServiceTypeId int IDENTITY(1,1) NOT NULL,
	ServiceTypeDesc varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TreatmentTypeId int NOT NULL,
	DefBillingRate decimal(10,2) NULL,
	DefServiceCode varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsBillable bit DEFAULT 1 NOT NULL,
	Siteid int NOT NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	CreateDate datetime DEFAULT getdate() NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsMasterFlag bit NULL,
	EarningCodeId int DEFAULT 0 NULL,
	IsNotAllowedOT bit DEFAULT 0 NOT NULL,
	IsPayable bit DEFAULT 1 NOT NULL,
	Color varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsSoapNote bit DEFAULT 0 NOT NULL,
	Abbreviation varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsActive bit DEFAULT 1 NOT NULL,
	IsNotCalculateBreakTime bit DEFAULT 0 NOT NULL,
	MaxDurationMinutes int NULL,
	IsShowSignatureInParentPortal bit DEFAULT 1 NOT NULL,
	IsConsiderAsSupervision bit DEFAULT 0 NOT NULL,
	IsServiceSubTypeMandatory bit DEFAULT 0 NOT NULL,
	IsNotinaddedTreatmentTeam bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK__ServiceT__8ADFAA6C3B3825AD PRIMARY KEY (ServiceTypeId),
    CONSTRAINT FK__ServiceTy__Sitei__160F4887 FOREIGN KEY (Siteid) REFERENCES AIStagingDB_20250811.dbo.Site(SiteId),
    CONSTRAINT FK__ServiceTy__Treat__17036CC0 FOREIGN KEY (TreatmentTypeId) REFERENCES AIStagingDB_20250811.dbo.TreatmentType(TreatmentTypeid)
);

-- Table: SeviceSubType
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.SeviceSubType (
	ServiceSubTypeId int IDENTITY(1,1) NOT NULL,
	ServiceSubTypeDesc varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
	ServiceTypeId int NOT NULL,
	SiteId int NULL,
	EarningCodeId int NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	CreateDate datetime NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	IsNotAllowedOT bit DEFAULT 0 NOT NULL,
	IsActive bit DEFAULT 1 NOT NULL,
	IsNotCalculateBreakTime bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK__SeviceSu__1C8DF5E3592E1126 PRIMARY KEY (ServiceSubTypeId),
    CONSTRAINT FK__SeviceSub__Servi__17F790F9 FOREIGN KEY (ServiceTypeId) REFERENCES AIStagingDB_20250811.dbo.ServiceType(ServiceTypeId)
);

-- Table: Site
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.Site (
	SiteId int IDENTITY(1,1) NOT NULL,
	DivisionId int NULL,
	Name varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LocationId int NULL,
	ActiveFrom datetime NULL,
	ActiveTo datetime NULL,
	CreateDate datetime NULL,
	CreatedBy int NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	EmailId varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	EIN varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	NPI varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DocPath varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TaxCode varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	StatusId int NULL,
	Password varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	Rate decimal(18,2) NULL,
	SiteContactName varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	sitemaincontactid int NULL,
	IsShowHideTimesheet bit DEFAULT 0 NOT NULL,
	PayrollSubmitMsg varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SftpUserName varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SftpPassword varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AlertDays int NULL,
	MileageRate decimal(18,3) NULL,
	ShowAppointment bit DEFAULT 0 NOT NULL,
	isofficesetting bit NULL,
	AutoPayrollTime bit DEFAULT 0 NULL,
	Ptresponsabilitynotes varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ptresponsabilitycreditinfoshow varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ptresponsabilitylocationid int NULL,
	SessionTimeout int DEFAULT 20 NOT NULL,
	IsEnableSms bit DEFAULT 0 NOT NULL,
	TimeZoneId varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	TimeZoneUtcOffset varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsFLSARuleorCARule bit DEFAULT 1 NOT NULL,
	LogoFileName varchar(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SoapNoteDisclaimer varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LogoId int NULL,
	PayrollSubmitEmailMsg varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PaymentPublicAPIKey nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PaymentPrivateAPIKey nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	InvoiceDueDays int NULL,
	SalesPersonId int NULL,
	InvoiceReceiver varchar(500) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PMSUpdate varchar(2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DCUpdate varchar(2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AvailabilityDisclaimer nvarchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	WaystarSFTPUserName varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	WaystarSftpPassword varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DCUpdateNotification varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MPMInvoiceNotification varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BillingNotification varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PMSUpdateNotification varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	SenderId837File varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ReceiverId837File varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsMobileOfflineModeEnabled bit DEFAULT 0 NOT NULL,
	DataCollectionStartDate datetime NULL,
	DataCollectionEndDate datetime NULL,
	SiteCurrency varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS DEFAULT '$' NULL,
	ShortName varchar(20) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsPartialDataEnabled bit DEFAULT 0 NOT NULL,
	MealBreakCnfMessage nvarchar(1024) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BigDataSftpUserName varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BigDataSftpPassword varchar(250) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	WalletID varchar(200) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsCompanyInvoiceAutoPay bit DEFAULT 0 NOT NULL,
	CompanyInvoicesComment varchar(2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	LeaveCCMail varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsNoBreakTime bit DEFAULT 0 NULL,
	BillingAutoClosingAmount decimal(10,2) NULL,
	MyAppointmentMessage varchar(160) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MyAvailabityCnfMessage varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	MPMInvoiceNotificationPhone varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	PMSUpdateNotificationPhone varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	DCUpdateNotificationPhone varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	BillingNotificationPhone varchar(MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AvalonSFTPUserName nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	AvalonSFTPPassword nvarchar(1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	IsDateCollectionUsage bit DEFAULT 0 NOT NULL,
	IsKPIReportEnabled bit DEFAULT 0 NOT NULL,
	IsMotivity bit DEFAULT 0 NOT NULL,
	MotivitySite varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	ExternalId varchar(50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
	CalenderFilterRecordLimit int DEFAULT 150 NOT NULL,
	IsCaspEnabled bit DEFAULT 0 NOT NULL,
	InvoiceProcessingMonths int DEFAULT 6 NULL,
	PRInvoiceMonths int DEFAULT 6 NULL,
	CONSTRAINT PK__Site__B9DCB963967BFC43 PRIMARY KEY (SiteId),
    CONSTRAINT FK_Site_Division FOREIGN KEY (DivisionId) REFERENCES AIStagingDB_20250811.dbo.Division(DivisionId)
);

-- Table: ZoneLocationMapping
-- Auto-generated description placeholder
CREATE TABLE AIStagingDB_20250811.dbo.ZoneLocationMapping (
	ZoneLocationMappingId int IDENTITY(1,1) NOT NULL,
	ZoneId int NOT NULL,
	LocationId int NOT NULL,
	CreateDate datetime DEFAULT getdate() NOT NULL,
	CreatedBy int NOT NULL,
	UpdateDate datetime NULL,
	UpdatedBy int NULL,
	CONSTRAINT PK__ZoneLoca__267308F78520962E PRIMARY KEY (ZoneLocationMappingId),
    CONSTRAINT FK__ZoneLocat__Locat__212CC0CF FOREIGN KEY (LocationId) REFERENCES AIStagingDB_20250811.dbo.Location(LocationId)
);

