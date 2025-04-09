# run this code in the terminal
# activate environment: micromamba activate mayavi
# start with: ipython --gui=qt5

from mayavi import mlab
import numpy as np
import nibabel as nb
import imageio.v2 as imageio
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import trimesh
from tvtk.api import tvtk
import os

# === USER INPUT: Path to the reference NIfTI image ===
# <-- Replace with your NIfTI file
nifti_image_path_1 = "/Users/amelie/Datasets/clinical_dmri_benchmark/MNI/mni_1mm_t1w_lps_brain.nii.gz"

# === USER INPUT: Path to the left and right hemisphere pial surfaces ===
mni_pial_left = "/Users/amelie/Datasets/clinical_dmri_benchmark/surfaces/tpl-fsLR_den-164k_hemi-L_midthickness.surf.gii"
mni_pial_right = "/Users/amelie/Datasets/clinical_dmri_benchmark/surfaces/tpl-fsLR_den-164k_hemi-R_midthickness.surf.gii"

# === USER INPUT: Root atlas bundles ===
atlas_bundle_root = "/Users/amelie/Datasets/clinical_dmri_benchmark/Atlas_Bundles"

# === USER INPUT: Root population maps ===
population_map_root = "/Users/amelie/Datasets/clinical_dmri_benchmark/overlay_maps"

# === USER INPUT: Output directory ===
# This script generates many larger files which are therefore not saved within the github repro
output_dir = "/Users/amelie/Datasets/clinical_dmri_benchmark/overlay_maps/population_over_atlas"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

bundles = [
    "Association_ArcuateFasciculusL",
    "Association_ArcuateFasciculusR",
    "Association_CingulumL",
    "Association_CingulumR",
    "Association_ExtremeCapsuleL",
    "Association_ExtremeCapsuleR",
    "Association_FrontalAslantTractL",
    "Association_FrontalAslantTractR",
    "Association_HippocampusAlveusL",
    "Association_HippocampusAlveusR",
    "Association_InferiorFrontoOccipitalFasciculusL",
    "Association_InferiorFrontoOccipitalFasciculusR",
    "Association_InferiorLongitudinalFasciculusL",
    "Association_InferiorLongitudinalFasciculusR",
    "Association_MiddleLongitudinalFasciculusL",
    "Association_MiddleLongitudinalFasciculusR",
    "Association_ParietalAslantTractL",
    "Association_ParietalAslantTractR",
    "Association_SuperiorLongitudinalFasciculusL",
    "Association_SuperiorLongitudinalFasciculusR",
    "Association_UncinateFasciculusL",
    "Association_UncinateFasciculusR",
    "Association_VerticalOccipitalFasciculusL",
    "Association_VerticalOccipitalFasciculusR",
    "Commissure_AnteriorCommissure",
    "Commissure_CorpusCallosum",
    "ProjectionBasalGanglia_AcousticRadiationL",
    "ProjectionBasalGanglia_AcousticRadiationR",
    "ProjectionBasalGanglia_AnsaLenticularisL",
    "ProjectionBasalGanglia_AnsaLenticularisR",
    "ProjectionBasalGanglia_AnsaSubthalamicaL",
    "ProjectionBasalGanglia_AnsaSubthalamicaR",
    "ProjectionBasalGanglia_CorticostriatalTractL",
    "ProjectionBasalGanglia_CorticostriatalTractR",
    "ProjectionBasalGanglia_FasciculusLenticularisL",
    "ProjectionBasalGanglia_FasciculusLenticularisR",
    "ProjectionBasalGanglia_FasciculusSubthalamicusL",
    "ProjectionBasalGanglia_FasciculusSubthalamicusR",
    "ProjectionBasalGanglia_FornixL",
    "ProjectionBasalGanglia_FornixR",
    "ProjectionBasalGanglia_OpticRadiationL",
    "ProjectionBasalGanglia_OpticRadiationR",
    "ProjectionBasalGanglia_ThalamicRadiationL",
    "ProjectionBasalGanglia_ThalamicRadiationR",
    "ProjectionBrainstem_CorticobulbarTractL",
    "ProjectionBrainstem_CorticobulbarTractR",
    "ProjectionBrainstem_CorticopontineTractL",
    "ProjectionBrainstem_CorticopontineTractR",
    "ProjectionBrainstem_CorticospinalTractL",
    "ProjectionBrainstem_CorticospinalTractR",
    "ProjectionBrainstem_DentatorubrothalamicTract-lr",
    "ProjectionBrainstem_DentatorubrothalamicTract-rl",
    "ProjectionBrainstem_MedialForebrainBundleL",
    "ProjectionBrainstem_MedialForebrainBundleR",
    "ProjectionBrainstem_MedialLemniscusL",
    "ProjectionBrainstem_MedialLemniscusR",
    "ProjectionBrainstem_NonDecussatingDentatorubrothalamicTractL",
    "ProjectionBrainstem_NonDecussatingDentatorubrothalamicTractR",
    "ProjectionBrainstem_ReticularTractL",
    "ProjectionBrainstem_ReticularTractR",
]

SURFACE_COLOR = (0.8, 0.8, 0.8)
FIGSIZE = (1600, 1080)

LH_LATERAL_CAMERA_POS_WORLD = np.array([86.0, -17.0, 15.0, 1.0])
LH_MEDIAL_CAMERA_POS_WORLD = np.array([-124.0, -17.0, 15.0, 1.0])
RH_LATERAL_CAMERA_POS_WORLD = np.array([34.0, -17.0, 15.0, 1.0])
RH_MEDIAL_CAMERA_POS_WORLD = np.array([126.0, -17.0, 15.0, 1.0])
SUP_CAMERA_POS_WORLD = np.array([2.0, -9.0, 13.0, 1.0])
POST_CAMERA_POS_WORLD = np.array([1.0, -17.0, 15.0, 1.0])

# === Load the NIfTI image and get the affine transformation ===
nii_img = nb.load(nifti_image_path_1)
affine = nii_img.affine  # 4x4 affine transformation matrix
# Invert the affine to map MNI -> voxel space
inv_affine = np.linalg.inv(affine)

# For the left hemisphere only
LH_LATERAL_CAMERA_VIEW = (0, 90.0, 360.0, list(
    inv_affine @ LH_LATERAL_CAMERA_POS_WORLD)[0:3])
LH_LATERAL_CAMERA_ROLL = -90.0
# Increase x to make the camera zoom in
LH_MEDIAL_CAMERA_VIEW = (180.0, 90.0, 360.0, list(
    inv_affine @ LH_MEDIAL_CAMERA_POS_WORLD)[0:3])
LH_MEDIAL_CAMERA_ROLL = 90.0


# For the right hemisphere only
RH_LATERAL_CAMERA_VIEW = (180.0, 90.0, 244.9, list(
    inv_affine @ RH_LATERAL_CAMERA_POS_WORLD)[0:3])
RH_LATERAL_CAMERA_ROLL = 90.0
RH_MEDIAL_CAMERA_VIEW = (0.0, 90.0, 360.0, list(
    inv_affine @ RH_MEDIAL_CAMERA_POS_WORLD)[0:3])
RH_MEDIAL_CAMERA_ROLL = -90.0


SUP_CAMERA_VIEW = (-90, 12, 336, list(inv_affine @ SUP_CAMERA_POS_WORLD)[0:3])
SUP_CAMERA_ROLL = -180

POST_CAMERA_VIEW = (90.0, 75.0, 280.0, list(
    inv_affine @ POST_CAMERA_POS_WORLD)[0:3])
POST_CAMERA_ROLL = 180

LEFT_VIEWS = ["lh_lateral", "lh_medial", "sup", "post"]
RIGHT_VIEWS = ["rh_lateral", "rh_medial", "sup", "post"]
BOTH_VIEWS = ["lh_lateral", "lh_medial",
            "rh_lateral", "rh_medial", "sup", "post"]


def transform_to_voxel_space(
    surface_file, inv_affine, subdivide=2, smooth_iters=20, simplify_ratio=None
):
    """Transforms GIFTI surface coordinates to voxel space using a NIfTI affine.

    Args:
        surface_file: Path to GIFTI surface file
        inv_affine: 4x4 inverse affine matrix
        subdivide: Number of subdivision iterations (0 for no subdivision)
        smooth_iters: Number of Laplacian smoothing iterations (0 for no smoothing)
        simplify_ratio: Target ratio of final to original faces (e.g., 0.5 for half)
    """
    gifti_surf = nb.load(surface_file)
    coords = gifti_surf.darrays[0].data  # Extract vertex coordinates
    faces = gifti_surf.darrays[1].data  # Get triangle faces

    # Create a trimesh mesh
    mesh = trimesh.Trimesh(vertices=coords, faces=faces)

    if simplify_ratio is not None:
        # Convert target ratio to reduction ratio (e.g., 0.5 -> 0.5 reduction)
        reduction = 1.0 - simplify_ratio
        # Simplify the mesh
        mesh = mesh.simplify_quadric_decimation(reduction)

    if subdivide > 0:
        # Perform subdivision
        for _ in range(subdivide):
            mesh = mesh.subdivide()

    if smooth_iters > 0:
        # Perform Laplacian smoothing
        mesh = mesh.smoothed(method="laplacian", iterations=smooth_iters)

    # Get processed vertices and faces
    coords = mesh.vertices
    faces = mesh.faces

    # Convert to homogeneous coordinates (add a column of 1s for affine multiplication)
    coords_homogeneous = np.hstack([coords, np.ones((coords.shape[0], 1))])

    # Apply inverse affine transformation (MNI space -> voxel space)
    voxel_coords = (inv_affine @ coords_homogeneous.T).T[:, :3]

    return voxel_coords, faces


def visualize_surface(voxel_coords, faces, color):
    """Visualizes the transformed surface in voxel space using Mayavi."""
    # Create a wire mesh surface with more transparent lines
    mesh = mlab.triangular_mesh(
        voxel_coords[:, 0],
        voxel_coords[:, 1],
        voxel_coords[:, 2],
        faces,
        color=color,
        representation='wireframe',  # Show as wireframe
        line_width=0.5,             # Thinner lines
        opacity=0.4                 # More transparent lines
    )


# Transform surfaces to voxel space with simplification
left_voxel_coords, left_faces = transform_to_voxel_space(
    mni_pial_left,
    inv_affine,
    subdivide=0,
    smooth_iters=0,
    simplify_ratio=0.3,  # Reduce to 30% of original faces
)
right_voxel_coords, right_faces = transform_to_voxel_space(
    mni_pial_right,
    inv_affine,
    subdivide=0,
    smooth_iters=0,
    simplify_ratio=0.3,  # Reduce to 30% of original faces
)

def camera_callback(obj, evt):
    """Print camera position whenever it changes"""
    # Get current view parameters
    view = mlab.view()
    roll = mlab.roll()

    if view is not None:  # view can be None before the scene is set up
        azimuth, elevation, distance, focalpoint = view
        print(f"\nCamera Position Updated:")
        print(f"Azimuth: {azimuth:.1f}")
        print(f"Elevation: {elevation:.1f}")
        print(f"Distance: {distance:.1f}")
        print(f"Focal Point: {focalpoint}")
        print(f"Roll: {roll:.1f}")

        # Print a ready-to-use mlab.view() command
        print(f"\nTo reproduce this view:")
        print(
            f"mlab.view({azimuth:.1f}, {elevation:.1f}, {distance:.1f}, {focalpoint.tolist()})"
        )
        print(f"mlab.roll({roll:.1f})")


def plot_bundle_opacity(
    data,
    data_atlas,
    output_file,
    interactive=True,
    figure=None,
    view="lh_lateral",
    max_opacity=1.0,
    min_opacity=0.5,
):
    # Use existing figure or create new one
    if figure is None:
        figure = mlab.figure(bgcolor=(1, 1, 1))
    else:
        # Clear existing figure
        mlab.clf()
        # Set background color
        figure.scene.background = (1, 1, 1)

    # Add the surfaces with light gray color
    if view.startswith("lh_"):
        visualize_surface(left_voxel_coords, left_faces, color=SURFACE_COLOR)
        if view.endswith("lateral"):
            _view = LH_LATERAL_CAMERA_VIEW
            _roll = LH_LATERAL_CAMERA_ROLL
        elif view.endswith("medial"):
            _view = LH_MEDIAL_CAMERA_VIEW
            _roll = LH_MEDIAL_CAMERA_ROLL
    elif view.startswith("rh_"):
        visualize_surface(right_voxel_coords, right_faces, color=SURFACE_COLOR)
        if view.endswith("lateral"):
            _view = RH_LATERAL_CAMERA_VIEW
            _roll = RH_LATERAL_CAMERA_ROLL
        elif view.endswith("medial"):
            _view = RH_MEDIAL_CAMERA_VIEW
            _roll = RH_MEDIAL_CAMERA_ROLL
    elif view.startswith("sup"):
        _view = SUP_CAMERA_VIEW
        _roll = SUP_CAMERA_ROLL
        visualize_surface(left_voxel_coords, left_faces, color=SURFACE_COLOR)
        visualize_surface(right_voxel_coords, right_faces, color=SURFACE_COLOR)
    elif view.startswith("post"):
        _view = POST_CAMERA_VIEW
        _roll = POST_CAMERA_ROLL
        visualize_surface(left_voxel_coords, left_faces, color=SURFACE_COLOR)
        visualize_surface(right_voxel_coords, right_faces, color=SURFACE_COLOR)
    else:
        raise ValueError(f"Invalid view: {view}")

    # Plot the atlas bundle
    if data_atlas is not None:
        contour = mlab.contour3d(
            data_atlas,
            contours=[0.1],
            color=(0.4, 0.4, 0.4),
            opacity=0.5,     # Lower starting opacity
            transparent=True
        )

        # Enable depth peeling for better transparency
        contour.actor.property.backface_culling = True
        contour.scene.renderer.use_depth_peeling = True
        contour.scene.renderer.maximum_number_of_peels = 100
        contour.scene.renderer.occlusion_ratio = 0.0

        # Get the VTK source and convert to polydata
        src = contour.mlab_source.dataset
        geometry_filter = tvtk.GeometryFilter()
        geometry_filter.set_input_data(src)
        geometry_filter.update()

        # Apply smoothing to the polydata
        smooth = tvtk.SmoothPolyDataFilter()
        smooth.set_input_data(geometry_filter.output)
        smooth.number_of_iterations = 10
        smooth.relaxation_factor = 0.5
        smooth.update()

        # Update the contour with smoothed data
        contour.mlab_source.dataset = smooth.output

    # plot the population map of reconstructed bundles
    if data is not None:
        # Get data range
        data_min = data.min()
        data_max = data.max()

        # Define fixed contour values and their colors (darker, more saturated)
        contour_specs = [
            (0.2, (0.0, 0.7, 0.9)),    # Bright blue
            (0.4, (0.0, 0.4, 0.8)),    # Medium blue
            (0.6, (0.4, 0.0, 0.8)),    # Purple
            (0.8, (0.8, 0.0, 0.4)),    # Red
        ]

        # Only add contours that fall within the data range
        for val, color in contour_specs:
            if data_min <= val <= data_max:
                # Scale opacity from 0.3 (lowest value) to 0.99 (highest value)
                opacity = 0.3 + (0.99 - 0.3) / (1 + np.exp(-8 * (val - 0.7)))

                contour = mlab.contour3d(
                    data,
                    contours=[val],
                    color=color,
                    opacity=opacity,     # Lower starting opacity
                    transparent=True
                )

                # Enable depth peeling for better transparency
                contour.actor.property.backface_culling = True
                contour.scene.renderer.use_depth_peeling = True
                contour.scene.renderer.maximum_number_of_peels = 100
                contour.scene.renderer.occlusion_ratio = 0.0

                # Get the VTK source and convert to polydata
                src = contour.mlab_source.dataset
                geometry_filter = tvtk.GeometryFilter()
                geometry_filter.set_input_data(src)
                geometry_filter.update()

                # Apply smoothing to the polydata
                smooth = tvtk.SmoothPolyDataFilter()
                smooth.set_input_data(geometry_filter.output)
                smooth.number_of_iterations = 10
                smooth.relaxation_factor = 0.5
                smooth.update()

                # Update the contour with smoothed data
                contour.mlab_source.dataset = smooth.output

    if interactive:
        mlab.gcf().scene.camera.add_observer("ModifiedEvent", camera_callback)
        mlab.show()
    else:
        mlab.view(*_view)
        mlab.roll(_roll)

        # Ensure the scene is rendered before saving
        mlab.gcf().scene.render()
        mlab.savefig(output_file, size=FIGSIZE)

    return output_file


def combine_pngs(png_files, output_file, text_label=""):
    """Combine 6 PNG files into a 2x3 grid and add text label.

    Args:
        png_files: List of 6 PNG file paths
        output_file: Output PNG file path
        text_label: Text to add in top right corner
    """
    # Verify all files exist and can be read
    for f in png_files:
        print(f)
        if not Path(f).exists():
            print(f"Warning: File not found: {f}")
            return None

    # Read all images
    images = []
    for f in png_files:
        try:
            img = imageio.imread(f)
            if img is None:
                print(f"Warning: Could not read image: {f}")
                return None
            images.append(img)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            return None

    if len(images) != 6:
        print(f"Warning: Expected 6 images, got {len(images)}")
        return None

    # Get dimensions of first image
    h, w = images[0].shape[:2]
    channels = images[0].shape[2] if len(images[0].shape) > 2 else 1

    # Create blank canvas matching input image format
    combined = np.zeros((h * 2, w * 3, channels), dtype=np.uint8)

    # Place images in grid
    for idx, img in enumerate(images):
        row = idx // 3  # 0 for first row, 1 for second row
        col = idx % 3  # 0, 1, 2 for columns
        combined[row * h: (row + 1) * h, col * w: (col + 1) * w] = img

    # Convert to PIL Image for text rendering
    pil_image = Image.fromarray(combined)
    draw = ImageDraw.Draw(pil_image)

    # Try to load Helvetica font, fall back to default if not available
    try:
        font = ImageFont.truetype("Helvetica", 120)
    except OSError:
        font = ImageFont.load_default()

    # Calculate text dimensions and center position
    text_bbox = draw.textbbox((0, 0), text_label, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Calculate center position (total width is w * 3, total height is h * 2)
    text_position = (
        (w * 3 - text_width) // 2,  # Center horizontally
        (h * 2 - text_height) // 2,  # Center vertically
    )

    # Draw text with white background for better visibility
    text_bg_bbox = (
        text_position[0] - 5,  # x1
        text_position[1] - 5,  # y1
        text_position[0] + text_width + 5,  # x2
        text_position[1] + text_height + 5,  # y2
    )
    draw.rectangle(text_bg_bbox, fill=(255, 255, 255, 255))
    draw.text(text_position, text_label, font=font, fill=(0, 0, 0, 255))

    # Save combined image
    imageio.imwrite(output_file, np.array(pil_image))

    return output_file


# Main part
fig = mlab.figure(bgcolor=(1, 1, 1), size=FIGSIZE)

# Take a dummy picture
mlab.gcf().scene.render()
mlab.savefig("test.png", size=FIGSIZE)

# Do it a second time so we have a correct image size
mlab.gcf().scene.render()
mlab.savefig("test.png", size=FIGSIZE)

os.remove("test.png")


ALL_VIEWS = ["rh_lateral", "rh_medial",
            "sup", "lh_lateral", "lh_medial", "post"]

for reconstruction in ["GQI", "CSD", "SS3T"]:
    for bundle_name in bundles:

        if os.path.exists(f"{output_dir}/{bundle_name}_{reconstruction}.png"):
            continue

        if bundle_name.endswith("L"):
            bundle_views = LEFT_VIEWS
        elif bundle_name.endswith("R"):
            bundle_views = RIGHT_VIEWS
        else:
            bundle_views = BOTH_VIEWS

        bundlename = bundle_name.replace("_", "").replace("-", "")
        img = nb.load(
            f"{population_map_root}/{reconstruction}autotrack/{bundlename}.nii.gz")
        img_atlas = nb.load(f"{atlas_bundle_root}/{bundle_name}_MNIc.nii.gz")
        data = img.get_fdata()
        data_atlas = img_atlas.get_fdata()
        view_pngs = {}
        for view in ALL_VIEWS:
            view_pngs[view] = []
            _data = data if view in bundle_views else None
            _data_atlas = data_atlas if view in bundle_views else None
            view_pngs[view].append(
                plot_bundle_opacity(
                    _data,
                    _data_atlas,
                    output_file=f"{bundle_name}_{reconstruction}_{view}.png",
                    interactive=False,
                    figure=fig,
                    view=view,
                )
            )

        # Assemble all the views into a single image for each time point
        combined_pngs = []
        combined_pngs.append(
            combine_pngs(
                [view_pngs[view][0] for view in ALL_VIEWS],
                output_file=f"{output_dir}/{bundle_name}_{reconstruction}.png",
            )
        )
        # Delete the intermediate files
        for view in ALL_VIEWS:
            for png in view_pngs[view]:
                Path(png).unlink()

        # Read images and resize them to 70% of original size
        images = []
        for f in combined_pngs:
            if f is None:
                print("Warning: Found None filename in combined_pngs")
                continue
            if not Path(f).exists():
                print(f"Warning: File not found: {f}")
                continue
            img = Image.fromarray(imageio.imread(f))
            # Calculate new dimensions (25% of original)
            new_width = int(img.width * 0.25)
            new_height = int(img.height * 0.25)
            # Resize image with high quality resampling
            resized_img = img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS)
            images.append(np.array(resized_img))
