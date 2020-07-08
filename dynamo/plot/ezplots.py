import numpy as np
import matplotlib.pyplot as plt
from ..tools.utils import flatten, isarray
from ..tools.Markov import smoothen_drift_on_grid


def plot_X(X, dim1=0, dim2=1, dim3=None, create_figure=False, figsize=(6, 6), sort_by_c='raw', **kwargs):
    if create_figure:
        plt.figure(figsize=figsize)
    
    x, y = X[:, dim1], X[:, dim2]
    c = kwargs.pop('c', None)
    if c is not None and isarray(c) and sort_by_c is not None:
        if sort_by_c == 'raw':
            i_sort = np.argsort(c)
        else:
            i_sort = np.argsort(np.abs(c))
        x = x[i_sort]
        y = y[i_sort]
        c = c[i_sort]
        if dim3 is not None: 
            z = X[:, dim3][i_sort]

    if dim3 is None:        
        plt.scatter(x, y, c=c, **kwargs)
    else:
        from mpl_toolkits.mplot3d import Axes3D
        plt.gcf().add_subplot(111, projection='3d')
        plt.gca().scatter(x, y, z, c=c, **kwargs)


def plot_V(X, V, dim1=0, dim2=1, create_figure=False, figsize=(6, 6), **kwargs):
    if create_figure:
        plt.figure(figsize=figsize)
    plt.quiver(X[:, dim1], X[:, dim2], V[:, dim1], V[:, dim2])


def zscatter(adata, basis='umap', layer='X', dim1=0, dim2=1, dim3=None,
    color=None, c_layer=None, sort_by_c=1, cbar_shrink=0.4, axis_off=True, **kwargs):

    if layer is None or len(layer) == 0:
        emb = basis
    else:
        emb = '%s_%s'%(layer, basis)
    X = adata.obsm[emb]
    if color in adata.var.index:
        title = color
        if c_layer is None:
            color = flatten(adata[:, color].X)
        else:
            color = flatten(adata[:, color].layers[c_layer])
    elif color in adata.obs.keys():
        title = color
        color = flatten(np.array(adata.obs[color])) 
    else:
        title = None

    plot_X(X, dim1=dim1, dim2=dim2, dim3=dim3, c=color, sort_by_c=sort_by_c, **kwargs)
    if isarray(color):
        plt.colorbar(shrink=cbar_shrink)
    if title is not None:
        plt.title(title)

    if axis_off:
        plt.axis('off')


def zstreamline(adata, basis="umap", v_basis=None, x_layer='X', v_layer='velocity',
    dim1=0, dim2=1, 
    color='k', create_figure=False, figsize=(6, 4),
    grid_num=50, smoothness=1, min_vel_mag=1e-5, return_grid=False,
    linewidth=1, constant_lw=False, density=1, **streamline_kwargs):
    
    if x_layer is None or len(x_layer) == 0:
        emb = basis
    else:
        emb = '%s_%s'%(x_layer, basis)
    v_basis = basis if v_basis is None else v_basis
    if v_layer is None or len(v_layer) == 0:
        v_emb = v_basis
    else:
        v_emb = '%s_%s'%(v_layer, v_basis)
    X = adata.obsm[emb][:, [dim1, dim2]]
    V = adata.obsm[v_emb][:, [dim1, dim2]]

    # set up grids
    #if np.isscalar(grid_num):
    #    grid_num = grid_num * np.ones(2)
    V_grid, X_grid = smoothen_drift_on_grid(X, V, n_grid=grid_num, smoothness=smoothness)
    V_grid, X_grid = V_grid.T, X_grid.T

    streamplot_kwargs = {
        "density": density*2,
        "arrowsize": 1,
        "arrowstyle": "fancy",
        "minlength": 0.5,
        "maxlength": 4.0,
        "integration_direction": "both",
        "zorder": 3,
    }

    mass = np.sqrt((V_grid**2).sum(0))
    # velocity filtering
    if min_vel_mag is not None:
        min_vel_mag = np.clip(min_vel_mag, None, np.quantile(mass, 0.4))
    mass[mass<min_vel_mag] = np.nan

    if not constant_lw:
        linewidth *= 2 * mass / mass[~np.isnan(mass)].max()
        linewidth = linewidth.reshape(grid_num, grid_num)
    streamplot_kwargs.update({"linewidth": linewidth})
    streamplot_kwargs.update(streamline_kwargs)

    x = X_grid[0].reshape(grid_num, grid_num)
    y = X_grid[1].reshape(grid_num, grid_num)
    u = V_grid[0].reshape(grid_num, grid_num)
    v = V_grid[1].reshape(grid_num, grid_num)
    if create_figure: plt.figure(figsize=figsize)
    plt.streamplot(x, y, u, v, color=color, **streamplot_kwargs)
    #plt.set_arrow_alpha(axes_list[i], streamline_alpha)
    #set_stream_line_alpha(s, streamline_alpha)
    if return_grid:
        return X_grid, V_grid