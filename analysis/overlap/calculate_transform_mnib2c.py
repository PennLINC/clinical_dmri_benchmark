# IMPORT STUFF
from niworkflows.interfaces.reportlets.base import (
    RegistrationRC,
    _SVGReportCapableInputSpec,
)
from niworkflows.interfaces.norm import (
    SpatialNormalization,
    _SpatialNormalizationInputSpec,
)
from nipype.interfaces.base import (
    traits,
)
from nipype.interfaces import ants
from nipype.interfaces.mixins import reporting
from nipype import (
        Node,
        logging
    )


LOGGER = logging.getLogger("nipype.interface")

# DEFINE THE FUNCTION
class RobustMNINormalizationInputSpecRPT(
    _SVGReportCapableInputSpec,
    _SpatialNormalizationInputSpec,
):
    # Template orientation.
    orientation = traits.Enum(
        "LPS",
        mandatory=True,
        usedefault=True,
        desc="modify template orientation (should match input image)",
    )


class RobustMNINormalizationOutputSpecRPT(
    reporting.ReportCapableOutputSpec,
    ants.registration.RegistrationOutputSpec,
):
    # Try to work around TraitError of "undefined 'reference_image' attribute"
    reference_image = traits.File(desc="the output reference image")


class RobustMNINormalizationRPT(RegistrationRC, SpatialNormalization):
    input_spec = RobustMNINormalizationInputSpecRPT
    output_spec = RobustMNINormalizationOutputSpecRPT

    def _post_run_hook(self, runtime):
        # We need to dig into the internal ants.Registration interface
        self._fixed_image = self._get_ants_args()["fixed_image"]
        if isinstance(self._fixed_image, (list, tuple)):
            self._fixed_image = self._fixed_image[0]  # get first item if list

        if self._get_ants_args().get("fixed_image_mask") is not None:
            self._fixed_image_mask = self._get_ants_args().get("fixed_image_mask")
        self._moving_image = self.aggregate_outputs(runtime=runtime).warped_image
        LOGGER.info(
            "Report - setting fixed (%s) and moving (%s) images",
            self._fixed_image,
            self._moving_image,
        )

        return super(RobustMNINormalizationRPT, self)._post_run_hook(runtime)

if __name__ == "__main__":
    
    # MAKE THE NODE AND DEFINE INPUTS
    anat_norm_interface = RobustMNINormalizationRPT(float=True, generate_report=True, flavor="precise")
    anat_nlin_normalization = Node(anat_norm_interface, name="anat_nlin_normalization")
    anat_nlin_normalization.base_dir = "/cbica/projects/clinical_dmri_benchmark/data/atlas_bundles"
    anat_nlin_normalization.inputs.orientation = "LPS"
    # The T1w images used to calculate the transform can be downloaded from templateflow using datalad
    anat_nlin_normalization.inputs.template = "/cbica/projects/clinical_dmri_benchmark/data/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
    anat_nlin_normalization.inputs.reference_image = "/cbica/projects/clinical_dmri_benchmark/data/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_T1w.nii.gz"
    anat_nlin_normalization.inputs.moving_image = "/cbica/projects/clinical_dmri_benchmark/data/templateflow/tpl-MNI152NLin2009bAsym/tpl-MNI152NLin2009bAsym_res-1_T1w.nii.gz"
    # Run it
    anat_nlin_normalization.run()