fprintf(1,'Executing %s at %s:\n',mfilename,datestr(now));
ver,
try,
if isempty(which('spm')),
throw(MException('SPMCheck:NotFound','SPM not in matlab path'));
end;
spm_path = spm('dir');
[name, version] = spm('ver');
fprintf(1, 'NIPYPE path:%s|name:%s|release:%s', spm_path, name, version);
exit;
        
,catch ME,
fprintf(2,'MATLAB code threw an exception:\n');
fprintf(2,'%s\n',ME.message);
if length(ME.stack) ~= 0, fprintf(2,'File:%s\nName:%s\nLine:%d\n',ME.stack.file,ME.stack.name,ME.stack.line);, end;
end;