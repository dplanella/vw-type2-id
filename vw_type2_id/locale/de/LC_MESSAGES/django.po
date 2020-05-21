msgid ""
msgstr ""
"Project-Id-Version: vw-type2-id\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2020-05-10 11:19+0000\n"
"PO-Revision-Date: 2020-05-21 01:02\n"
"Last-Translator: David Planella <david.planella@gmail.com>\n"
"Language-Team: German\n"
"Language: de\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: Poedit 2.3\n"
"X-Crowdin-Project: vw-type2-id\n"
"X-Crowdin-Language: de\n"
"X-Crowdin-File: /master/vw_type2_id/locale/ca/LC_MESSAGES/django.po\n"

#: mplate_decoder/forms.py:61
#, python-brace-format
msgid "Minimum digits: {MODEL_6869_YEAR_CHASSIS_NR_LEN} (mod. 68-68) or {MODEL_7079_YEAR_CHASSIS_NR_LEN} digits (mod. 70-79)"
msgstr ""

#: mplate_decoder/forms.py:66
msgid "Only digits allowed, without spaces. The second digit is always a 2."
msgstr ""

#: mplate_decoder/forms.py:77
msgid "Invalid shortened chassis number. Check first digit."
msgstr ""

#: mplate_decoder/forms.py:83
msgid "Invalid shortened chassis number. Check first and second digits."
msgstr ""

#: mplate_decoder/forms.py:106
#, python-brace-format
msgid "M-Plate already exists. View {mplate_link}."
msgstr ""

#: mplate_decoder/forms.py:116
msgid "Only the letter 'E' is allowed"
msgstr ""

#: mplate_decoder/forms.py:128
msgid "Only digits, letters and spaces allowed"
msgstr ""

#: mplate_decoder/forms.py:140
#, python-brace-format
msgid "Code: {mcode}. M-code length should be {MCODE_LEN} digits or letters"
msgstr ""

#: mplate_decoder/forms.py:145
#, python-brace-format
msgid "Minimum M-code length: {MCODE_LEN} digits or letters"
msgstr ""

#: mplate_decoder/forms.py:167 mplate_decoder/forms.py:242
msgid "Only digits and letters allowed"
msgstr ""

#: mplate_decoder/forms.py:171
#, python-brace-format
msgid "Minimum paint and interior code length: {PAINT_AND_INTERIOR_LEN} digits or letters"
msgstr ""

#: mplate_decoder/forms.py:195
msgid "Cannot validate production date format without a valid chassis number."
msgstr ""

#: mplate_decoder/forms.py:204 mplate_decoder/forms.py:221
msgid "Invalid production date format. Please double check."
msgstr ""

#: mplate_decoder/forms.py:212
msgid "Invalid production date. Please double check."
msgstr ""

#: mplate_decoder/forms.py:215
#, python-brace-format
msgid "Invalid production date ({exc}). Please double check."
msgstr ""

#: mplate_decoder/forms.py:226
msgid "Invalid production week date. Please double check  the two first digits."
msgstr ""

#: mplate_decoder/forms.py:246
#, python-brace-format
msgid "Minimum destination country length: {EXPORT_DESTINATION_LEN} letters or digits"
msgstr ""

#: mplate_decoder/forms.py:257
#, python-brace-format
msgid "Minimum model code length: {MODEL_LEN} digits"
msgstr ""

#: mplate_decoder/forms.py:267
#| msgid "Model year"
msgid "Invalid model. Please double check."
msgstr ""

#: mplate_decoder/forms.py:272
msgid "Only digits allowed in model code"
msgstr ""

#: mplate_decoder/forms.py:277
#| msgid "Model year"
msgid "Invalid model code"
msgstr ""

#: mplate_decoder/forms.py:287
msgid "Minimum aggregate code length: "
msgstr ""

#: mplate_decoder/forms.py:296
msgid "Only digits allowed in aggregate code"
msgstr ""

#: mplate_decoder/forms.py:309
msgid "Invalid aggregate code"
msgstr ""

#: mplate_decoder/models.py:27
msgid "Shortened chassis number"
msgstr ""

#: mplate_decoder/models.py:29
msgid "Chassis number shortened, with the two leading digits removed."
msgstr ""

#: mplate_decoder/models.py:32
msgid "M-codes, row 1"
msgstr ""

#: mplate_decoder/models.py:34
msgid "Row 1 of M codes (max 5)"
msgstr ""

#: mplate_decoder/models.py:36
msgid "M-codes, row 2"
msgstr ""

#: mplate_decoder/models.py:38
msgid "Row 2 of M codes (max 4 -mod. '70-'79 or 5 -mod. '68-'69-)"
msgstr ""

#: mplate_decoder/models.py:41
msgid "Paint and interior"
msgstr ""

#: mplate_decoder/models.py:43
msgid "Combined VW body/roof paint and interior codes"
msgstr ""

#: mplate_decoder/models.py:45
msgid "Production date"
msgstr ""

#: mplate_decoder/models.py:47
msgid "Production date code"
msgstr ""

#: mplate_decoder/models.py:49
msgid "Production planning"
msgstr ""

#: mplate_decoder/models.py:51
msgid "Production planning code"
msgstr ""

#: mplate_decoder/models.py:53
msgid "Export destination"
msgstr ""

#: mplate_decoder/models.py:55
msgid "Export destination code"
msgstr ""

#: mplate_decoder/models.py:57
msgid "Vehicle model"
msgstr ""

#: mplate_decoder/models.py:59
msgid "Vehicle model code"
msgstr ""

#: mplate_decoder/models.py:61
msgid "Aggregate"
msgstr ""

#: mplate_decoder/models.py:63
msgid "Engine and gearbox aggregate code"
msgstr ""

#: mplate_decoder/models.py:65
msgid "Emden"
msgstr ""

#: mplate_decoder/models.py:67
msgid "Optional \"E\" for Emden"
msgstr ""

#: mplate_decoder/models.py:84
msgid "Full list of M codes for this M plate"
msgstr ""

#: mplate_decoder/models.py:87
msgid "Planned production date, in time format"
msgstr ""

#: mplate_decoder/models.py:90
msgid "Model year"
msgstr ""

#: mplate_decoder/models.py:93
msgid "Country of destination"
msgstr ""

#: mplate_decoder/models.py:227
#, python-brace-format
msgid "({interiorcolor_code}) Unknown color"
msgstr ""

#: mplate_decoder/models.py:228
msgid "Unknown material"
msgstr ""

#: mplate_decoder/models.py:240
msgid "Error while fetching interior color code:"
msgstr ""

#: mplate_decoder/models.py:241
#, python-brace-format
msgid " {interiorcolor_code}, year {model_year}"
msgstr ""

#: mplate_decoder/models.py:247
msgid "No description available for special paint jobs"
msgstr ""

#: mplate_decoder/models.py:266
msgid "Unavailable engine description"
msgstr ""

#: mplate_decoder/models.py:282
msgid "Unavailable transmission description"
msgstr ""

#: mplate_decoder/models.py:335
#, python-brace-format
msgid "MplateDecoder requires an mplate or {attribute_name}"
msgstr ""

#: mplate_decoder/models.py:388
msgid "MplateDecoder requires an mplate or model code"
msgstr ""

#: mplate_decoder/models.py:400
msgid "MplateDecoder requires an mplate or model year"
msgstr ""

#: mplate_decoder/models.py:407
msgid "MplateDecoder requires an mplate or M codes"
msgstr ""

#: mplate_decoder/models.py:510
#, python-brace-format
msgid "Invalid model year code length: {model_year_code_len}, code {model_year_code}, chassis no. {chassis_number_short}"
msgstr ""

#: mplate_decoder/models.py:531
msgid "MplateDecoder requires either an m-plate or chassis_number with encoded production date"
msgstr ""

#: mplate_decoder/models.py:630
msgid "MplateDecoder requires an mplate or mcodes_1/m_codes_2"
msgstr ""

#: mplate_decoder/models.py:638
msgid "MplateDecoder requires an mplate or chassis_number_short"
msgstr ""

#: mplate_decoder/models.py:675
#, python-brace-format
msgid "Unknown code, year {model_year}"
msgstr ""

#: mplate_decoder/models.py:684
#, python-brace-format
msgid "Undefined code, year {model_year}"
msgstr ""

#: mplate_decoder/models.py:751 mplate_decoder/models.py:801
#| msgid "Export destination code"
msgid "Unknown ({export_destination_code})"
msgstr ""

#: mplate_decoder/models.py:785
msgid "Undefined country or region"
msgstr ""

#: mplate_decoder/models.py:866
#, python-brace-format
msgid "Unknown exterior color code ({exteriorcolor_code})"
msgstr ""

#: mplate_decoder/models.py:877
#, python-brace-format
msgid "Unknown color ({exteriorcolor.lacquer_code_body})"
msgstr ""

#: mplate_decoder/models.py:888
#, python-brace-format
msgid "Unknown color ({exteriorcolor.lacquer_code_roof})"
msgstr ""

#: mplate_decoder/models.py:894
#, python-brace-format
msgid "Remarks: {exteriorcolor.remarks}"
msgstr ""

#: mplate_decoder/models.py:897
#, python-brace-format
msgid "Body: {color_name_body} ({exteriorcolor.lacquer_code_body})\n"
"            Roof: {color_name_roof} ({lacquer_code_roof})"
msgstr ""

#: mplate_decoder/models.py:983 mplate_decoder/models.py:997
#: mplate_decoder/models.py:1043
msgid "List of M-codes for the corresponding extras"
msgstr ""

#: mplate_decoder/models.py:1038
msgid "Model description"
msgstr ""

#: mplate_decoder/models.py:1047
msgid "Model description as it appears on the chassis plate"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/mplate_about.html:10
msgid "\n"
"## About this site\n\n"
"This site provides means to identify and understand the origin of Volkswagen Type 2 busses\n"
"from years 1967 to 1979. At this time, via an online M-Plate decoder, but it might expand in the future.\n"
"M-Plates were metallic plates present in all VW busses, which contained a set of alphanumeric production\n"
"codes to identify a vehicle.\n\n"
"The site was created as a result of the [original VW M-Plate decoder](https://web.archive.org/web/20181005162116/http://www.vw-mplate.com/mcode.php)\n"
"going offline, as a personal project to decode the author's own M-Plate and to experiment with code. From there,\n"
"it evolved into a public website to share this tool with other vintage bus owners from the aircooled community. \n\n"
"The data used to decode the M-plates comes mainly from these sources, and keeps getting expanded every time a user finds out more about\n"
"an unknown code and shares it with the community:\n\n"
"- [VW Transporter and Microbus, Specification Guide 1967-1979](https://www.crowood.com/details.asp?isbn=9781847974808) - by Vincent Molenaar and Alexander Prinz\n"
"- [TheSamba.com forum](https://www.thesamba.com/vw/forum/viewforum.php?f=5)\n"
"- [forum.bulli.org forum](https://forum.bulli.org/)\n"
"- [type2.com](http://www.type2.com/m-codes/t2mcodes.html)\n"
"- [Rolf-Stephan Badura's VW T2 Bulli site](https://www.vw-t2-bulli.de)\n\n"
"Thanks so much to the authors of those resources and to everyone who share their knowledge. The M-plate decoder would not have been possible without that vast collaborative effort.\n\n"
"## Privacy policy\n\n"
"This is a hobby site without a commercial purpose and without intention to seek financial profit. The stored database data\n"
"will never be submitted to third parties or used for other purposes than improving the site and providing a better\n"
"service to its users.\n\n"
"The code for this site is Open Source. You can explore it and contribute\n"
"to the [`vw-type2-id` project on GitLab](https://gitlab.com/vw-type2/vw-type2-id).\n\n"
"The site's backend has a database that stores:\n\n"
"- The original data submitted through the M-plate form, along with some of the decoded values computed from that data (e.g. model year in readable form).\n"
"- The creation date and last update date of the submitted M-plate data.\n"
"- If the user has chosen to create an account on the site, their user name, e-mail and last login date.\n\n"
"If you've used this service without creating an account and would like to have the data for a particular M-plate removed or amended, feel free to [contact the author](#contact).\n"
"If you have created an account, you already have full control over your data and should be able to either remove or change the data on the `My M-plates` section.\n\n"
"## Disclaimer\n\n"
"The decoded vehicle data produced on this site comes from multiple sources. Despite best efforts to provide accurate data,\n"
"it has to be noted that it comes from volunteer research over 40+ years of history of these vehicles.\n\n"
"As such, data is neither guaranteed to be accurate nor to have any legal validity. It should be considered as orientative\n"
"only.\n\n"
"## Contact\n\n"
"If you've got feedback or questions about the site, feel free to [get in touch](/contact).\n\n"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:13
msgid "Code"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:14
msgid "Years"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:15
msgid "Description"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:26
msgid "M-code collection:"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:34
#: mplate_decoder/templates/mplate_decoder/search_results.html:35
#: mplate_decoder/views.py:435
msgid "Unknown"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:42
#, python-format
msgid "Found %(count)s M-plates with M-code:"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:46
msgid "M-plate"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:47
msgid "M-codes"
msgstr ""

#: mplate_decoder/templates/mplate_decoder/search_results.html:105
msgid "There are currently no M-plates with M-code:"
msgstr ""

#: mplate_decoder/urls.py:31
msgid "VW Type 2 ID"
msgstr ""

#: mplate_decoder/urls.py:32
#, python-brace-format
msgid "{SITE_NAME} Admin"
msgstr ""

#: mplate_decoder/urls.py:33
#, python-brace-format
msgid "{SITE_NAME} Admin Portal"
msgstr ""

#: mplate_decoder/urls.py:34
#, python-brace-format
msgid "Welcome to {SITE_NAME} Admin Portal"
msgstr ""

#, fuzzy
#~| msgid "Model year"
#~ msgid "Invalid model year "
#~ msgstr "Any de model"

