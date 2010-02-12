function doc = spm_get_doc(docname)
% Get the documentation from SPM for the functionality named
% docname.
%
% This will search through the spm_config() object and grab the
% documentation whose name matches docname.
cfgstruct = spm_flat_config(0);
[rows, cols] = size(cfgstruct);
docstruct.help={'None'};
% Loop over cell array and search for the docname
for i = 1:cols
  if strcmp(cfgstruct{i}.name, docname)
    docstruct = cfgstruct{i};
    break
  end
end
% Add a tag so we can strip off the Matlab header information and
% only print out the SPM documentation.
tag = 'NIPYPE\n';
doc = strcat(tag, docstruct.help{:});
end
