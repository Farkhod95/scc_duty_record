from django.urls import re_path, path

from .views.department import DepartmentView, DepartmentDetailView, DepartmentFieldInfoView
from .views.district import DistrictView, DistrictDetailView, DistrictFieldInfoView

from .views.mahalla import MahallaView, MahallaDetailView, MahallaFieldInfoView
from .views.organization import OrganizationView, OrganizationDetailView, OrganizationFieldInfoView
from .views.position import PositionView, PositionDetailView, PositionFieldInfoView
from .views.region import RegionView, RegionDetailView, RegionFieldInfoView

from .views.special_rank import SpecialRankView, SpecialRankDetailView, SpecialRankFieldInfoView

from directory.views.location import LocationView, LocationDetailView, LocationFieldInfoView

urlpatterns = [
    re_path(r'^special-rank/$', SpecialRankView.as_view(), name='special_rank_view'),
    path('special-rank/<int:pk>', SpecialRankDetailView.as_view(), name='special_rank_detail_view'),
    path('special-rank/fields/', SpecialRankFieldInfoView.as_view(), name='special_rank_fields_info'),

    re_path(r'^region/$', RegionView.as_view(), name='regions_view'),
    path('region/<int:pk>', RegionDetailView.as_view(), name='region_detail_view'),
    path('region/fields/', RegionFieldInfoView.as_view(), name='region_fields_info'),

    re_path(r'^district/$', DistrictView.as_view(), name='districts_view'),
    path('district/<int:pk>', DistrictDetailView.as_view(), name='districts_detail_view'),
    path('district/fields/', DistrictFieldInfoView.as_view(), name='district_fields_info'),


    re_path(r'^organization/$', OrganizationView.as_view(), name='organization_view'),
    path('organization/<int:pk>', OrganizationDetailView.as_view(), name='organization_detail_view'),
    path('organization/fields/', OrganizationFieldInfoView.as_view(), name='organization_fields_info'),



    re_path(r'^position/$', PositionView.as_view(), name='position_view'),
    path('position/<int:pk>', PositionDetailView.as_view(), name='position_detail_view'),
    path('position/fields/', PositionFieldInfoView.as_view(), name='position_fields_info'),

    re_path(r'^mahalla/$', MahallaView.as_view(), name='mahalla_view'),
    path('mahalla/<int:pk>', MahallaDetailView.as_view(), name='mahalla_detail_view'),
    path('mahalla/fields/', MahallaFieldInfoView.as_view(), name='mahalla_fields_info'),


    re_path(r'^department/$', DepartmentView.as_view(), name='department_view'),
    path('department/<int:pk>', DepartmentDetailView.as_view(), name='department_detail_view'),
    path('department/fields/', DepartmentFieldInfoView.as_view(), name='department_fields_info'),

    re_path(r'^location/$', LocationView.as_view(), name='location_view'),
    path('location/<int:pk>', LocationDetailView.as_view(), name='location_detail_view'),
    path('location/fields/', LocationFieldInfoView.as_view(), name='location_fields_info'),
]