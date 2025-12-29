filename define "your-path\define.xml";
filename extract "your-path\extract-list-ds.xsl";
filename dsjson "your-path\transform-to-ds-json.xsl";
filename tmpxml temp;

proc xsl in=define
         xsl=extract
         out=tmpxml;
run;

data _null_;
  infile tmpxml truncover;
  input line $32000.;
  call symputx('xslResult', line);
run;

%macro loop;
    %let i = 1;
    %let value = %scan(%bquote(&xslResult.), &i., %str(,));

    %do %while(%length(&value.));

		data _null_;
			dt = datetime();
			call symputx('datasetJSONCreationDateTime', cats(put(datepart(dt), yymmdd10.), 'T', put(timepart(dt), time8.)));
		run;

		proc xsl in=define
		         xsl=dsjson
		         out="your-path\&value..json";
			parameter 'dsName'="&value." 'datasetJSONCreationDateTime' = "&datasetJSONCreationDateTime.";
		run;

        %let i = %eval(&i. + 1);
        %let value = %scan(%bquote(&xslResult.), &i., %str(,));
    %end;
%mend;

%loop;
