*KEYWORD
*TITLE
crash box HC340LA t=1.5mm h=5mm 500kg @ 15m/s
$ units: mm / ms / kg / kN / GPa   (energy in kN-mm = J)
$ element size 5 mm, wall thickness 1.5 mm, material HC340LA
$ acceptance: hourglass < 5% and added mass < 5% of the model mass
*CONTROL_TERMINATION
$#  endtim    endcyc     dtmin    endeng    endmas     nosol
      25.0         0       0.0       0.0       0.0         0
*CONTROL_TIMESTEP
$#  dtinit    tssfac      isdo    tslimt     dt2ms      lctm     erode     ms1st
       0.0       0.9         0       0.0   -0.0008         0         1         0
*CONTROL_ENERGY
$#    hgen      rwen    slnten     rylen     irgen
         2         2         2         2         2
*CONTROL_HOURGLASS
$#     ihq        qh
         4      0.05
*CONTROL_SHELL
$#  wrpang     esort     irnxx    istupd    theory       bwc     miter      proj
      20.0         1        -1         1         2         2         1         0
*CONTROL_CONTACT
$#  slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien    enmass
       0.1       0.0         2         1         4         1         1         0
$#  usrstr    usrfrc     nsbcs    interm     xpene     ssthk      ecdt   tiedprj
         0         0         0         0       4.0         0         0         0
*CONTROL_ACCURACY
$#     osu       inn    pidosu      iacc
         1         4         0         1
*DATABASE_GLSTAT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_MATSUM
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_RCFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SLEOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_NODOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_ELOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SECFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_SPCFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_RWFORC
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_BNDOUT
$#      dt    binary      lcur     ioopt
      0.05         3         0         1
*DATABASE_BINARY_D3PLOT
$#      dt      lcdt      beam     npltc    psetid
       0.5         0         0         0         0
*DATABASE_EXTENT_BINARY
$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
         0         0        -3         1         1         1         1         1
$#  cmpflg    ieverp    beamip     dcomp      shge     stssz    n3thdt   ialemat
         0         1         0         1         2         3         2         1
*DATABASE_HISTORY_NODE_SET
        11
*PART
crash box HC340LA t=1.5
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         1         1         1         0         1         0         0         0
*PART
rigid impactor
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         2         2         2         0         0         0         0         0
*SECTION_SHELL_TITLE
tube, type 16 fully integrated
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         1        16    0.8333         5       1.0       0.0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.5       1.5       1.5       1.5       0.0       0.0       0.0         0
*SECTION_SHELL_TITLE
impactor plate
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         2         2    0.8333         2       1.0       0.0         0         1
$#      t1        t2        t3        t4
       5.0       5.0       5.0       5.0
*HOURGLASS
$#    hgid       ihq        qm       ibq        q1        q2    qb/vdc        qw
         1         4      0.05         0       1.5      0.06       0.0       0.0
*DEFINE_CURVE_TITLE
HC340LA effective stress vs plastic strain [GPa]
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
       100         0       1.0       1.0       0.0       0.0         0         0
                 0.0               0.355
       0.00474341649               0.355
        0.0134164079         0.373494645
        0.0246475151         0.405708382
        0.0379473319         0.432480258
        0.0530330086         0.455425794
        0.0697137002         0.475569522
        0.0878493028         0.493577592
         0.107331263         0.509902884
         0.128072245         0.524866269
                0.15         0.538703208
          0.17305346         0.551591638
         0.197180121         0.563669383
         0.222334208         0.575045452
         0.248475351         0.585807618
         0.275567596         0.596027649
         0.303578655         0.605765023
         0.332479323         0.615069615
         0.362243012         0.623983684
         0.392845389         0.632543373
         0.424264069         0.640779848
         0.456478368         0.648720187
           0.4894691         0.656388076
         0.523218406          0.66380436
         0.557709602         0.670987491
         0.592927061         0.677953881
         0.628856104         0.684718202
         0.665482907         0.691293626
         0.702794422         0.697692026
         0.740778307         0.703924144
         0.779422863         0.709999734
         0.818716984         0.715927681
         0.858650103         0.721716103
         0.899212155         0.727372438
         0.940393535         0.732903522
         0.982185064          0.73831565
          1.02457796         0.743614632
          1.06756382         0.748805849
          1.11113456         0.753894287
          1.15528243         0.758884581
                 1.2         0.763781046
*MAT_PIECEWISE_LINEAR_PLASTICITY_TITLE
HC340LA (representative flow curve)
$#     mid        ro         e        pr      sigy      etan      fail      tdel
         1   7.85e-6     210.0       0.3     0.355       0.0       0.0       0.0
$#       c         p      lcss      lcsr        vp
       8.0       5.0       100         0       1.0
$#    eps1      eps2      eps3      eps4      eps5      eps6      eps7      eps8
       0.0       0.0       0.0       0.0       0.0       0.0       0.0       0.0
$#     es1       es2       es3       es4       es5       es6       es7       es8
       0.0       0.0       0.0       0.0       0.0       0.0       0.0       0.0
*MAT_RIGID_TITLE
impactor
$#     mid        ro         e        pr         n    couple         m     alias
         2 0.0069444     210.0       0.3       0.0       0.0       0.0       0.0
$#     cmo      con1      con2
       1.0         4         7
$#  lco/a1        a2        a3        v1        v2        v3
       0.0       0.0       0.0       0.0       0.0       0.0
*BOUNDARY_SPC_SET
$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
        10         0         1         1         1         1         1         1
*INITIAL_VELOCITY_GENERATION
$#      id      styp     omega        vx        vy        vz     ivatn      icid
         2         2       0.0       0.0       0.0     -15.0         0         0
$#      xc        yc        zc        nx        ny        nz     phase    irigid
       0.0       0.0       0.0       0.0       0.0       0.0         0         0
*SET_PART_LIST
        20       0.0       0.0       0.0       0.0
         1
*SET_PART_LIST
        21       0.0       0.0       0.0       0.0
         2
*CONTACT_AUTOMATIC_SINGLE_SURFACE_ID
         1self contact of the folding tube
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        20         0         2         0         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
       0.2      0.15       0.0       0.0      20.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         2         0         1
*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE_ID
         2impactor to tube
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
        20        21         2         2         0         0         1         1
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
      0.15       0.1       0.0       0.0      20.0         0       0.0    1.0e20
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
$#    soft    sofscl    lcidab    maxpar     sbopt     depth     bsort    frcfrq
         1       0.1         0     1.025       2.0         2         0         1
*INCLUDE
mesh_h5.k
*END
