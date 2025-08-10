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
