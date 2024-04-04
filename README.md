# Clinical dMRI postprocessing benchmarking

There are many clinical scans with 16-30 directions at b=1000. They will likely have susceptibility distortion and lots of head motion. 
We want to see exactly what kind of derivatives we can reliably extract from these kinds of scans.

## Specialized preprocessing

The PNC dataset acquired two 32-direction b=1000 dMRI scans. 
There is also a GRE fieldmap that can be applied to both scans independently.
We can process these two scans completely separately using the `--separate-all-dwis`
flag in QSIPrep. Specifically these steps

  * MP-PCA denoising
  * Susceptibility distortion correction
  * Eddy current and head motion correction
  * Coregistration to T1w image
  * b1 bias field correction

will be run separately for both images, simulating how they would be processed if 
they were standalone clinical dMRI scans.

### Synthetic distortion correction?

One potential follow-up question about preprocessing is whether a synthetic 
fieldmap could work as well as the GRE fieldmaps in PNC.
One approach could be to use SyNb0 DISCO. 
This isn't implemented in QSIPrep yet though :(

## QC measures

Important QC measures, such as neighboring DWI Correlation (NDC) and 
contrast to noise ration (CNR) will be critical to this study. 
Head motion parameters and outlieriness are also calculated by Eddy.
These are by default included for each scan in QSIPrep outputs. 
_Any other QC measures we should include?_

## Tractometry

Tractometry from AutoTrack will be a primary outcome variable for this study.
It may or may not be able to find bundles depending on the input data. 
We want to know 

 1. Which bundles are difficult to reconstruct, regardless of input data quality?
 2. Are certain bundles only reliably reconstructable above a certain quality threshold?
 3. Are there shared properties of reconstructable bundles (eg AP, long projections, which cortical regions they hit)
 4. Are there properties of bundles (volume, curvature, fanning) that vary as a function
    of data quality?
 5. For reliably-reconstructable bundles, do any of these properties correlate with
    personality or cognitive variables?
    


## File organization on CUBIC

```
/path/to/project/
    |-  code/           # Local clone of the GitHub repository
        |-  figures/    # Any figures for the manuscript
        |_  data/       # Tabular data that may be shared on GitHub
    |-  data/
    |-  results/        # Results that cannot be shared on GitHub
    |_  reproduction/
        |-  code/       # Local clone of reproducibilibuddy's fork of GitHub repository
        |-  data/       # Any data that must be copied and not referenced
        |_  results/
```
