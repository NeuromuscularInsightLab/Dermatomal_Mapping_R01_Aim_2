function NORDIC_run_single_file(in_nii, out_nii, nordic_path)
% Run NORDIC on exactly ONE NIfTI:
%   in_nii  -> out_nii
%
% out_nii must end with .nii.gz (to match write_gzipped_niftis=1).

if ~isfile(in_nii)
    error('Input not found: %s', in_nii);
end

if ~isfolder(nordic_path)
    error('nordic_path not found: %s', nordic_path);
end

if ~endsWith(out_nii, '.nii.gz')
    error('out_nii must end with .nii.gz : %s', out_nii);
end

[out_dir, out_name, out_ext] = fileparts(out_nii); %#ok<ASGLU>  % out_ext will be '.gz'
if ~isfolder(out_dir)
    mkdir(out_dir);
end

% out_name is like 'something.nii' for a .nii.gz path
out_stem = regexprep(out_name, '\.nii$', '');

addpath(genpath(nordic_path));
assert(exist('NIFTI_NORDIC','file')==2, 'NIFTI_NORDIC not found on path. Check NORDIC_PATH.');

% ---- NORDIC parameters (edit here when needed) ----
ARG.magnitude_only       = 1;
ARG.temporal_phase       = 1;
ARG.phase_filter_width   = 10;
ARG.NORDIC               = 1;
ARG.MP                   = 1;
ARG.full_dynamic_range   = 0;
ARG.write_gzipped_niftis = 1;
ARG.kernel_size_gfactor  = [7 7 7 300];
ARG.kernel_size_PCA      = [7 7 7];
ARG.factor_error         = 1.0;

ARG.DIROUT = [out_dir filesep];

fprintf('NORDIC: %s -> %s\n', in_nii, out_nii);

% magnitude-only: dummy phase = same file
NIFTI_NORDIC(in_nii, in_nii, out_stem, ARG);

if ~isfile(out_nii)
    error('Expected output not found: %s', out_nii);
end
end