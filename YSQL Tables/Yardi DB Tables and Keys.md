Yardi DB Tables and Keys

Yardi DB API Document

Voyager 7S Data Dictionary_through update DB6327_052522.pdf

Yardi Native Useful Tables

Table Name: property

Data type- property level data like address ,Property ID etc.

Table Name: unit

Data type- unit name, exclude flag etc.

Table Name: UnitXRef (dim_fp_propertybusinessplancustomdata)

Data type- unit to amendment connection

Table Name: tenant

Data Type- Lease info like tenant name, start date, user defined fields like the SLB flag we added, end date etc.

Table Name: Attributes

Data Type- Property custom attributes attached to property like ACQ Status, AM, Fund, Entity, Market etc.

Table Name: CommAmendments

Data Type- Lease start/end date, leased SF etc.

iType NOT IN (6, 13) if want to filter out Modification and Deals

How to recognize M2M leases- DtEnd column becomes NULL and the iTerm column will be 0.

Table Name: CommPropMarketRent

Data Type- contains Property Valuations

Table Name: vendor

Data Type- Vendor info

Table Name: CommICS

NAICS codes map in the system

sCode column shows NAICS code, sDesc column shows description of NAICS code

Table Name: CommTenant

hCommICS column shows hmy of NAICS code

Table Name: Chargtyp

Charge code typed from rent schedule

Table Name: CAMRule

Charge schedule per charge code for each amendment - this is how we build rent roll

Useful Custom Tables

Table Name: PROBUT31

Data Type- Business Plan info

Table Name: PROPBUT_FAROPOINT

Data Type- Building physical info like clear height for example + Acq/Dispo dates etc.

Table Name: CUSTBUT1

Data Type- Credit Score data

Table Name: UnitBut1

Data Type- Unit physicals data : lights, HVAC, hazard materials, electric power etc.

Query Examples

Pull All Existing Building Physical Data from Custom Table

Export File Example

ySQL_0_09102024105859.csv

Query

SELECT p.SCODE, f.*

FROM PROPBUT_FAROPOINT f

JOIN property p ON f.hCode = p.HMY

Pull All Existing Business Plan Records

Export File Example

ySQL_0_17062024085922.csv

Query

SELECT p.SCODE, f.*

FROM PROPBUT31 f

JOIN property p ON f.hCode = p.HMY

All Lease Amendments with Property, Units, Fund identifiers

Filter Conditions

Filter out Model Properties and Leases

Filter in Sold and Acquired Properties only

Filter out cancelled or Deal related amendments

Export File Example

ySQL_0_17032025105829.csv

Query

QUERY All Lease Amendments with Property Units Fund identifiers.txt

All Lease Amendments with Property, Units, Fund identifiers, NAICS

Filter Conditions

Filter out Model Properties and Leases

Filter in Sold and Acquired Properties only

Filter out cancelled or Deal related amendments

Export File Example

ySQL_0_13022025112620.csv

Query

QUERY All Lease Amendments with Property Unit Fund identifiers NAICS.txt

All Lease Amendments- CLEAN with full mapping and all ID fields

Export Example

ySQL_0_25032025051307.csv

Query

QUERY All Lease Amendments- CLEAN with full mapping and all ID fields.txt

Physical Property (Building) Data for RECAP

Export Example

ySQL_0_09102024084241.csv

Query

QUERY Physical Property (Building) Data for RECAP.txt

Building Data for Monthly Report

Export Example

ySQL_0_09102024084150.csv

Query

QUERY Building Data for Monthly Report.txt

Unit Data for Monthly report

Export Example

ySQL_0_09102024084104.csv

Query

QUERY Unit Data for Monthly report.txt

Active units with address and market

Export Example

ySQL_0_09102024084023.csv

Query

SELECT

 LTRIM(RTRIM(a.SUBGROUP1)) AS "Market",

 LTRIM(RTRIM(p.SCODE)) AS "Property Code",

 LTRIM(RTRIM(p.Saddr2)) AS "Property Address",

 LTRIM(RTRIM(u.SCODE)) AS "Unit Code"

FROM unit u

JOIN property p ON u.HPROPERTY = p.HMY

JOIN attributes a ON a.HPROP = p.HMY

WHERE u.exclude NOT IN (-1)

 AND p.SCODE NOT LIKE 'mp%'

 AND a.SUBGROUP32 IN ('Acquired')

Mapping Property-Market-Asset Manager

Export Example

ySQL_0_09102024082800.csv

Query

SELECT 

p.SCODE AS "Property Code",

p.sAddr2 AS "Property Address",

a.SUBGROUP27 as "Fund",

a.SUBGROUP1 as "Market",

a.SUBGROUP32 as "Status",

a.SUBGROUP28 AS "Asset Manager"

FROM property p 

Join Attributes a ON p.HMY = a.HPROP

 WHERE 

  p.sCode NOT LIKE 'mp%'

  AND a.SUBGROUP32 IN ('Acquired')

Performance Table-Building data

Query

QUERY Performance Table-Building data.txt

Leases including: SLB Flag=YES, Customer Code, Property address

Export Example

ySQL_0_05112024010551.csv

Query

QUERY Leases including SLB Flag isYES Customer Code Property addressdata.txt

Leases including: SLB Flag, Customer Code, Property address

Export Example

ySQL_0_05112024010818.csv

Query

QUERY Leases including SLB Flag Customer Code Property address.txt

Tenant ID+ Customer ID + Latest credit score data per Tenant

Export Example

ySQL_0_27112024093619.csv

Query

QUERY Customer ID Name DB ID and Parent DB ID.txt

Customer ID ,Name, DB ID and Parent DB ID

Export Example

ySQL_0_20022025065130.csv

Query

QUERY Customer ID Name DB ID and Parent DB ID.txt

Property Valuations

Export Example

ySQL_0_13012025083043.csv

Query

QUERY Property Valuations.txt

Rent Schedule- Charge Code Types and GL Mapping

Export Example

ySQL_0_02042025064448.csv

Query

QUERY Rent Schedule- Charge Code Types and GL Mapping.txt

Charge Schedule for Amendment

Query

QUERY Charge Schedule for Amendment.txt

Unit to Amendment Mapping

Export Example

ySQL_0_02042025094043.csv

Query

QUERY Unit to Amendment Mapping.txt

FM MLA Report

Sample Data

Sample data.csv

Query

QUERY Fact_FP_FMVM_MarketUnitRates.txt

Leasing Activity Report as in Deal Manager

Query-Work in progress, not ready yet

QUERY Leasing Acivity Report.txt

List of properties to entity mapping- Report for GC

Export Example

ySQL_0_26062025084417.csv

Query

QUERY List of properties to entity mapping- Report for GC.txt