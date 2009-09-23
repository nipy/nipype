function doc = spm_get_doc(docname)
% Get the documentation from SPM for the functionality named
% docname.
%
% This will search through the spm_config() object and grab the
% documentation whose name matches docname.

% XXX put in a try-catch?  I'm finding matlab's exception handling
% a bit confusing.
cfg = spm_config();
cfgstruct = find_doc(cfg, docname);
hdr = 'NIPYPE\n';
doc = strcat(hdr, cfgstruct.help{:});
end


function docstruct = find_doc(astruct, docname)
% Find the structure that contains the documentation `docname`.

% Flatten the cfg structure
cfg_list = spm_cfg_list(astruct, {});
[rows, cols] = size(cfg_list);
% Loop over cell array and search for the docname
for i = 1:cols
  if strcmp(cfg_list{i}.name, docname)
    docstruct = cfg_list{i};
    break
  end
end
end


function objlist = spm_cfg_list(astruct, objlist)
% Flatten the nested structure in 'astruct'.
% Returns a cell array.
% Usage:  objlist = spm_cfg_list(astruct, {})

if isfield(astruct, 'values')
  [rows, cols] = size(astruct.values);
  for i = 1:cols
    objlist = spm_cfg_list(astruct.values{i}, objlist);
  end
else
  objlist = {objlist{:} astruct};
end
end