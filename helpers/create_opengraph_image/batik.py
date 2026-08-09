import image_helpers
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.ndimage import binary_erosion
from scipy.ndimage import binary_dilation
from scipy.ndimage import gaussian_filter
from scipy.ndimage import grey_dilation
from scipy.ndimage import map_coordinates
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE_DIR = HERE / "images"

class WaxResist:
    UNASSIGNED = -1
    BOUNDARY_ID = 0
    # Gradient Ascent/Descent Globals
    GD_EPSILON = 5e-2
    GD_MAX_ITER = 200
    GD_STEP_SIZE = 1
    JUNCTION_RADIUS = 10.0
    
    def __init__(self, wax: str | Path | np.ndarray):
        """Load the wax mask and initialize its boundary as feature zero."""
        if isinstance(wax, (str, Path)):
          self.wax_path = Path(wax)
          wax_mask = image_helpers.load_mask(self.wax_path)
        elif isinstance(wax, np.ndarray):
          if wax.ndim != 2 or wax.dtype != np.bool_:
            raise TypeError("wax arrays must be two-dimensional boolean arrays")
          self.wax_path = None
          wax_mask = wax
        else:
          raise TypeError("wax must be an image path or a boolean NumPy array")

        self.wax = wax_mask.copy()
        self.original_wax = wax_mask.copy()
        self.wax_indices = np.argwhere(self.wax)
        
        self.distance = np.full(self.wax.shape, np.inf, dtype=np.float64)
        self.distance_to_junction = np.full(self.wax.shape, np.inf, dtype=np.float64)
        self.junction_mask = np.zeros(self.wax.shape, dtype=bool)
        self.junction_source_strength = np.zeros(self.wax.shape, dtype=np.float64)
        self.junction_influence = np.zeros(self.wax.shape, dtype=np.float64)

        # These must exist before find_edge_of_wax() tries to use them.
        self.wax_border: np.ndarray | None = None
        self.crack_indices = np.full(self.wax.shape, self.UNASSIGNED, dtype=np.int32)
        self.newest_crack = self.UNASSIGNED

        self.find_edge_of_wax()

    def find_edge_of_wax(self):
        """Find and label the inner wax boundary, once."""
        if self.wax_border is not None:
            return self.wax_border

        self.outer_border = binary_dilation(self.wax) & ~self.wax

        self.wax_border = self.wax & ~binary_erosion(
            self.wax,
            border_value=0,
        )
        
        self.crack_indices[self.outer_border] = self.BOUNDARY_ID
        self.newest_crack = self.BOUNDARY_ID

    def distance_to_cracks(self):
        if self.wax_border is None:
            self.find_edge_of_wax()
        assert self.wax_border is not None
        
        # get euclidiean distance to nearest crack or edge of wax
        self.distance, self.nearest_indices = distance_transform_edt(
            self.wax,
            return_indices=True,
        )
    def distance_gradient(self, sigma = 3.0):
      smoothed_distance = gaussian_filter(self.distance, sigma=sigma)
      #smoothed_distance = self.distance
      self.gradient = np.gradient(smoothed_distance)
      
    def distance_hessian(self, sigma = 3.0):
      smoothed_gradient_0 = gaussian_filter(self.gradient[0], sigma=sigma)
      smoothed_gradient_1 = gaussian_filter(self.gradient[1], sigma=sigma)
      
      self.hessian =  (np.gradient(smoothed_gradient_0), np.gradient(smoothed_gradient_1))
      self.hessian_determinant = (
        self.hessian[0][0] * self.hessian[1][1]
        - self.hessian[0][1] * self.hessian[1][0]
      )
      
      
    def is_in_wax(self, point):
      return bool(map_coordinates(
          self.wax,
          point[:, np.newaxis],
          order=0,
          mode="constant",
          cval=False,
        )[0])

    def is_in_bounds(self, point):
      """Return whether a subpixel coordinate lies inside the image canvas."""
      point = np.asarray(point)
      return bool(
        point.shape == (2,)
        and np.isfinite(point).all()
        and 0.0 <= point[0] <= self.wax.shape[0] - 1
        and 0.0 <= point[1] <= self.wax.shape[1] - 1
      )

    def canvas_boundary_intersection(self, start, end):
      """Find where an in-bounds step first intersects the canvas boundary."""
      start = np.asarray(start, dtype=np.float64)
      end = np.asarray(end, dtype=np.float64)
      direction = end - start
      step_fraction = 1.0

      for axis, upper_bound in enumerate(np.asarray(self.wax.shape) - 1):
        if end[axis] < 0.0:
          step_fraction = min(
            step_fraction,
            (0.0 - start[axis]) / direction[axis],
          )
        elif end[axis] > upper_bound:
          step_fraction = min(
            step_fraction,
            (upper_bound - start[axis]) / direction[axis],
          )

      intersection = start + step_fraction * direction
      return np.clip(intersection, 0.0, np.asarray(self.wax.shape) - 1)
      
    def gradient_ascent(self, start, ascent = True, noisy = False, store_path = False):
      """
      Takes a 2-D coordinate and goes up or down the image's gradient map
      """
      if ascent:
        direction_scalar = 1.0
      else:
        direction_scalar = -1.0
        
      # to gradient **ascent** to find a local pixel that is high stress (biggest
      # distance to wax)
      q = np.asarray(start, dtype=np.float64).copy()
      if store_path:
        path = []
      i = 0
      Delta = np.inf
      while i < self.GD_MAX_ITER and Delta > self.GD_EPSILON:
        if not self.is_in_bounds(q):
          break

        if store_path:
          path.append(q.copy())

        # An in-canvas step outside the wax has reached another crack or the
        # wax boundary. Keep that endpoint, but do not take another step.
        if not self.is_in_wax(q):
          break
        
        # do update
        y_grad = map_coordinates(self.gradient[0], q[:, np.newaxis], order = 1)[0]
        x_grad = map_coordinates(self.gradient[1], q[:, np.newaxis], order = 1)[0]
        next_q = q + direction_scalar * self.GD_STEP_SIZE * np.array([y_grad, x_grad])
        if noisy:
          next_q += np.random.normal(0, .675, 2)
          
        Delta = np.max(np.abs((y_grad,x_grad)))
        i += 1

        # End the crack at the point where this step hits the canvas, rather
        # than retaining an out-of-bounds coordinate for record_crack().
        if not self.is_in_bounds(next_q):
          if np.isfinite(next_q).all():
            q = self.canvas_boundary_intersection(q, next_q)
            if store_path and not np.allclose(path[-1], q):
              path.append(q.copy())
          break

        q = next_q
        
        if i==self.GD_MAX_ITER:
          print("Bailing")
      

      if store_path:
        return q, np.asarray(path, dtype=np.float64).reshape(-1, 2)
      else:
        return q
      

    
    def find_next_crack(self):
      """
      Take the existing grid of distances and find a reasonable place for 
      the next crack to form. 
      """
      random_waxy_index = np.random.choice(len(self.wax_indices))
      crack_seed = self.wax_indices[random_waxy_index]
      
      return self.gradient_ascent(crack_seed, store_path = True)
      
      
    
    def grow_crack(self, crack_seed):
      """Take the seed location for a crack and grow the crack in both directions."""
      
      # The eigenvector of the hessian at this point tells us which direction to
      # go to most steeply descend. This is probably a bit more numerically
      # stable than the gradient which is likely near zero
      yy = map_coordinates(self.hessian[0][0], crack_seed[:, np.newaxis], order = 1)[0]
      yx = map_coordinates(self.hessian[0][1], crack_seed[:, np.newaxis], order = 1)[0]
      # xy = map_coordinates(self.hessian[1][0], crack_seed[:, np.newaxis], order = 1)[0]
      xx = map_coordinates(self.hessian[1][1], crack_seed[:, np.newaxis], order = 1)[0]
      crack_direction = np.linalg.eigh(np.array([
        [yy, yx],
        [yx, xx]
      ]))[1][0] # second component (eigenvector), first (most negative, evec)
      nudge = crack_direction * 1
      
      #y_nudge = map_coordinates(self.gradient[0], crack_seed[:, np.newaxis], order = 1)[0]
      #x_nudge = map_coordinates(self.gradient[1], crack_seed[:, np.newaxis], order = 1)[0]
      #nudge = 1 * np.array([y_nudge, x_nudge]) / np.sqrt((y_nudge**2) + (x_nudge**2))
      
      # nudge the quasi-optimal point so they move in opposite directions.
      up_start = crack_seed + nudge
      down_start = crack_seed - nudge
      
      up_output, up_path = self.gradient_ascent(up_start, ascent = False, noisy = True, store_path = True)
      down_output, down_path = self.gradient_ascent(down_start, ascent = False, noisy = True, store_path = True)
      
      endpoints = np.concatenate((up_output, down_output))
      # flips the order of one of the paths so it goes 
      # end ... mid mid ... end (as a crack would)
      path = np.concatenate((np.flip(up_path, axis=0), crack_seed[np.newaxis,:], down_path))
      
      return endpoints, path
    
    def record_crack(self, endpoints, subpixel_path):
      self.record_junctions(subpixel_path)

      midpoints = (subpixel_path[:-1] + subpixel_path[1:]) / 2 
      midpoints = midpoints[np.isfinite(midpoints).all(axis=1)]
      pixel_indices = np.rint(midpoints).astype(np.int32)
      in_bounds = (
        (pixel_indices[:, 0] >= 0)
        & (pixel_indices[:, 0] < self.wax.shape[0])
        & (pixel_indices[:, 1] >= 0)
        & (pixel_indices[:, 1] < self.wax.shape[1])
      )
      pixel_indices = pixel_indices[in_bounds]
      if len(pixel_indices) == 0:
        return

      pixel_indices = np.unique(pixel_indices, axis=0)
      coordinates = tuple(pixel_indices.T)
      self.wax[coordinates] = False
      # increment the crack counter
      self.newest_crack += 1
      self.crack_indices[coordinates] = self.newest_crack

    def record_junctions(self, subpixel_path):
      """Record endpoint widening values along the new crack."""
      if len(subpixel_path) < 2:
        return

      # compute the running distance of the crack and far it is from the beginning
      # and end of the crack, then take whichever is closer (up to some max distance)
      segment_lengths = np.linalg.norm(np.diff(subpixel_path, axis=0), axis=1)
      distance_from_start = np.concatenate(([0.0], np.cumsum(segment_lengths)))
      distance_from_end = distance_from_start[-1] - distance_from_start
      distance_to_junction = np.minimum(distance_from_start, distance_from_end)
      strength = np.maximum(0.0, self.JUNCTION_RADIUS - distance_to_junction)

      pixel_indices = np.rint(subpixel_path).astype(np.int32)
      
      # LLM generated random safety code I didn't ask for. Probably best to keep though
      valid = (
        np.isfinite(subpixel_path).all(axis=1)
        & (pixel_indices[:, 0] >= 0)
        & (pixel_indices[:, 0] < self.wax.shape[0])
        & (pixel_indices[:, 1] >= 0)
        & (pixel_indices[:, 1] < self.wax.shape[1])
      )
      pixel_indices = pixel_indices[valid]
      strength = strength[valid]
      if len(pixel_indices) == 0:
        return

      # overwrite any existing crack strengths if they're now bigger
      np.maximum.at(
        self.junction_source_strength,
        (pixel_indices[:, 0], pixel_indices[:, 1]),
        strength,
      )
      
      # record the pixels that are now being used as junctions
      endpoints = pixel_indices[[0, -1]]
      self.junction_mask[endpoints[:, 0], endpoints[:, 1]] = True

    def update_junction_fields(self):
      """Compute distance and widening influence from every recorded junction."""
      if not np.any(self.junction_mask):
        self.distance_to_junction.fill(np.inf)
        self.junction_influence.fill(0.0)
        return

      self.distance_to_junction = distance_transform_edt(~self.junction_mask)

      # Create a circular boolean mask to determine where cracks can have influence
      radius = int(np.ceil(self.JUNCTION_RADIUS))
      offsets = np.arange(-radius, radius + 1)
      dy, dx = np.meshgrid(offsets, offsets, indexing="ij")
      distance = np.hypot(dy, dx)
      footprint = distance <= self.JUNCTION_RADIUS
      structure = -distance
      
      # effectively blurs the existing on-crack source strengths
      # to neighboring pixels (so we can change dye properties in those spaces)
      self.junction_influence = np.maximum(
        0.0,
        grey_dilation(
          self.junction_source_strength,
          footprint=footprint,
          structure=structure,
          mode="constant",
          cval=-np.inf,
        ),
      )
      
    def add_cracks(self, n: int = 100):
      for i in range(n):
        self.distance_to_cracks()
        self.distance_gradient(sigma = 0)
        self.distance_hessian(sigma = 0)
        q, path = self.find_next_crack()
        endpoints, path = self.grow_crack(q)
        self.record_crack(endpoints, path)
      self.update_junction_fields()
      
    def compute_dye_concentration(self):
      """Compute how concentrated a dye *could* be on this resist. 0 if fully waxed
      1 if fully able to be dyed. We account for age of crack and proximity to junction
      in computing this"""

      self.distance_to_cracks()

      min_crack_width = 1.0
      max_crack_width = 3.0
      max_junction_width_boost = 5.0

      # Older cracks are wider. The previous age effect is retained as a smooth
      # interpolation between the minimum and maximum crack widths.
      age_effect_ceiling = 0.5
      crack_width_halving_period = 50
      nearest_y = self.nearest_indices[0]
      nearest_x = self.nearest_indices[1]
      nearest_crack_id = self.crack_indices[nearest_y, nearest_x].copy()
      nearest_crack_id[
        self.wax & (nearest_crack_id == self.UNASSIGNED)
      ] = self.BOUNDARY_ID
      # the id is effectively the iter num on which its nearest crack was generated
      age =  self.newest_crack - nearest_crack_id
      age_effect = age_effect_ceiling * (2**(-age/crack_width_halving_period))

      # blur effect so there's no weird discrete borders
      # but only do this for internal cracks
      age_blur = gaussian_filter(age_effect, sigma=5.0)
      new_cracks = (nearest_crack_id != self.BOUNDARY_ID) & (nearest_crack_id != self.UNASSIGNED)
      age_effect[new_cracks] = age_blur[new_cracks]

      age_width_fraction = np.clip(1.0 - age_effect, 0.0, 1.0)
      base_crack_width = (
        min_crack_width
        + (max_crack_width - min_crack_width) * age_width_fraction
      )
      junction_width = max_junction_width_boost * np.clip(
        self.junction_influence / self.JUNCTION_RADIUS,
        0.0,
        1.0,
      )
      self.effective_crack_width = base_crack_width + junction_width

      concentration = np.clip(
        1.0 - (self.distance / self.effective_crack_width),
        0.0,
        1.0,
      )
      # everything with literally no wax should have full intensity
      concentration[~self.wax] = 1.0

      self.concentration = concentration
    
      

    def show(self, img, points=None):
        plt.imshow(img)
        if points is not None:
            points = np.atleast_2d(points)
            plt.scatter(points[:, 1], points[:, 0], c="red", s=24)
        plt.axis("off")
        plt.show()

class Dye:
  MIN_TRANSMISSION = 1e-6

  def __init__(self, hex: str):
    """Create a dye from its full-strength appearance on white cloth."""
    if not isinstance(hex, str):
      raise TypeError("hex must be a string")

    value = hex.removeprefix("#")
    if len(value) != 6:
      raise ValueError("hex must contain exactly six hexadecimal digits")
    try:
      channels = np.array(
        [int(value[i:i + 2], 16) for i in (0, 2, 4)],
        dtype=np.float64,
      )
    except ValueError as error:
      raise ValueError("hex must contain exactly six hexadecimal digits") from error

    self.hex = f"#{value.lower()}"
    self.srgb = channels / 255.0
    self.linear_rgb = np.where(
      self.srgb <= 0.04045,
      self.srgb / 12.92,
      ((self.srgb + 0.055) / 1.055) ** 2.4,
    )

    # Light passes through a dye layer twice, so a full-strength layer uses a
    # single-pass transmission whose square equals the requested appearance.
    self.transmission = np.sqrt(self.linear_rgb)
    self.absorbance = -np.log(
      np.maximum(self.transmission, self.MIN_TRANSMISSION)
    )
  

class DyePass:
  def __init__(self, dye: Dye, wax: WaxResist, amount: np.ndarray | None = None):
      if not isinstance(dye, Dye):
        raise TypeError("dye must be of class Dye")
      if not isinstance(wax, WaxResist):
        raise TypeError("wax must be WaxResist")
      
      self.dye = dye
      self.wax = wax

      if not hasattr(wax, "concentration"):
        wax.compute_dye_concentration()

      if amount is None:
        self.amount = np.ones(wax.wax.shape, dtype=np.float64)
      else:
        amount = np.asarray(amount, dtype=np.float64)
        if amount.shape != wax.wax.shape:
          raise ValueError("amount must have the same height and width as the wax")
        if not np.isfinite(amount).all() or np.any((amount < 0) | (amount > 1)):
          raise ValueError("amount values must be finite and between 0 and 1")
        self.amount = amount.copy()

      effective_concentration = wax.concentration * self.amount
      self.transmission = 1 - (
        effective_concentration[:, :, np.newaxis] * (1 - dye.transmission)
      )
      
class BatikImage:
  def __init__(self, dye_passes: list[DyePass], base_color: str = "#ffffff"):
    if not dye_passes:
      raise ValueError("dye_passes must contain at least one DyePass")
    if not all(isinstance(layer, DyePass) for layer in dye_passes):
      raise TypeError("every layer must be a DyePass")

    shape = dye_passes[0].wax.wax.shape
    if any(layer.wax.wax.shape != shape for layer in dye_passes):
      raise ValueError("all dye passes must have the same image dimensions")

    self.dye_passes = list(dye_passes)
    self.base_color = Dye(base_color)
    self.linear_rgb = np.broadcast_to(
      self.base_color.linear_rgb,
      (*shape, 3),
    ).copy()

    for layer in self.dye_passes:
      self.linear_rgb *= layer.transmission ** 2

    self.linear_rgb = np.clip(self.linear_rgb, 0.0, 1.0)
    self.srgb = np.where(
      self.linear_rgb <= 0.0031308,
      12.92 * self.linear_rgb,
      1.055 * self.linear_rgb ** (1 / 2.4) - 0.055,
    )
    self.srgb = np.clip(self.srgb, 0.0, 1.0)
    self.rgb = np.rint(self.srgb * 255).astype(np.uint8)

  def save(self, path: str | Path):
    image_helpers.save_image(path, self.rgb)
  
  

def main():
  # set up seed
  seed = 0x436963616B2069732074686520626573742063617420696E2074686520776F726C64
  seed_small = np.random.SeedSequence(seed).generate_state(4)
  np.random.seed(seed_small)
  
  
  path = IMAGE_DIR / "redwood_mask.png"
  wax = WaxResist(path)
  
  # add the wax for the leaves then dye blue
  wax.add_cracks(1000)
  wax.compute_dye_concentration()
  dye = Dye("#000D4D")
  dye_pass = DyePass(dye, wax)
  
  # cover the entire canvas in wax, then dye green. So the only
  # trace of green should be in cracks
  new_mask = np.full(wax.wax.shape, True)
  wax2 = WaxResist(new_mask)
  wax2.add_cracks(100)
  wax2.compute_dye_concentration()
  dye2 = Dye("#55CE58")
  dye_pass2 = DyePass(dye2, wax2)
  
  batik = BatikImage([dye_pass, dye_pass2])
  IMAGE_DIR.mkdir(parents=True, exist_ok=True)
  batik.save(IMAGE_DIR / "batik_canvas.png")
  
  #breakpoint()
    
  # batik.show(batik.junction_source_strength)
  # batik.show(batik.junction_influence)
  # batik.show(batik.wax)
  # batik.distance_hessian(sigma = 3)
  # batik.show(batik.hessian[0][1])
  # batik.show(batik.distance)
  # #batik.show(batik.distance, path)
  # batik.show(batik.crack_indices)
  # batik.show(np.sqrt(batik.gradient[0]**2 + batik.gradient[1]**2))
  


if __name__ == "__main__":
  main()
