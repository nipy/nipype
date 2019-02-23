function cfgstruct = spm_flat_config(print_names)
% Get a flat spm_config structure, with option to print out names
%
% This calls spm_config() to get the the nested configuration
% structure from spm.  We use this to fetch documentation, the
% flattened structure is much easier to search through.  If
% print_names is true (value of 1) it will print out the configuration
% names. If print_names is false (value of 0), it will only return
% the flattened structure.
if strcmp(spm('ver'),'SPM5')
    cfg = spm_config();
else
    cfgstruct = [];
    return;
end
cfgstruct = spm_cfg_list(cfg, {});
if print_names
  [rows, cols] = size(cfgstruct);
  for i = 1:cols
    fprintf(1, '%d : %s\n', i, cfgstruct{i}.name)
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
