function parse_spm_config2

conf = spm_config;
sub_parse_config(spm_config)

function sub_parse_config(conf,level)
if nargin<2,
    level = 1;
end
if ~isfield(conf,'tag')
    level = level - 1;
else
    if ~strcmp(conf.type,'entry')
        fprintf(' %s- %s[%s] :\n\n',char(repmat('  ',1,level-1)),conf.tag,conf.type);
    else
        fprintf(' %s- %s[%s] :\n\n',char(repmat('  ',1,level-1)),conf.tag,conf.type);
    end
end
if isfield(conf,'values'),
    if ~isempty(strmatch('help',fieldnames(conf)))
    if isstr(conf.help),
        fprintf('\n %s ::\n %s\n',char(repmat(' ',1,level-1)),strrep(conf.help,'_','\_'));
    else
        for h0=1:numel(conf.help),
            fprintf('\n %s ::\n %s\n',char(repmat(' ',1,level-1)),strrep(conf.help{h0},'_','\_'));
        end
    end
    end
    for i0=1:numel(conf.values),
        if isstruct(conf.values{i0}),
            sub_parse_config(conf.values{i0},level+1)
        else
            if ischar(conf.values{i0})
                fprintf(' %s- [ %s : %s]\n\n',char(repmat('  ',1,level)),conf.labels{i0},conf.values{i0});
            else
                fprintf(' %s- [ %s : %s]\n\n',char(repmat('  ',1,level)),conf.labels{i0},num2str(conf.values{i0}));
            end
        end
    end
    
end
if isfield(conf,'val'),
    for i0=1:numel(conf.val),
        if isstruct(conf.val{i0}),
            sub_parse_config(conf.val{i0},level+1)
        else
            if ischar(conf.val{i0})
                fprintf(' %s- [default : %s]\n\n',char(repmat('  ',1,level)),conf.val{i0});
            else
                fprintf(' %s- [default : %s]\n\n',char(repmat('  ',1,level)),num2str(conf.val{i0}));
            end
        end
    end
end
