// Generated by gencpp from file ros_counteruav/fakedata.msg
// DO NOT EDIT!


#ifndef ROS_COUNTERUAV_MESSAGE_FAKEDATA_H
#define ROS_COUNTERUAV_MESSAGE_FAKEDATA_H


#include <string>
#include <vector>
#include <map>

#include <ros/types.h>
#include <ros/serialization.h>
#include <ros/builtin_message_traits.h>
#include <ros/message_operations.h>


namespace ros_counteruav
{
template <class ContainerAllocator>
struct fakedata_
{
  typedef fakedata_<ContainerAllocator> Type;

  fakedata_()
    : data(0)  {
    }
  fakedata_(const ContainerAllocator& _alloc)
    : data(0)  {
  (void)_alloc;
    }



   typedef int8_t _data_type;
  _data_type data;





  typedef boost::shared_ptr< ::ros_counteruav::fakedata_<ContainerAllocator> > Ptr;
  typedef boost::shared_ptr< ::ros_counteruav::fakedata_<ContainerAllocator> const> ConstPtr;

}; // struct fakedata_

typedef ::ros_counteruav::fakedata_<std::allocator<void> > fakedata;

typedef boost::shared_ptr< ::ros_counteruav::fakedata > fakedataPtr;
typedef boost::shared_ptr< ::ros_counteruav::fakedata const> fakedataConstPtr;

// constants requiring out of line definition



template<typename ContainerAllocator>
std::ostream& operator<<(std::ostream& s, const ::ros_counteruav::fakedata_<ContainerAllocator> & v)
{
ros::message_operations::Printer< ::ros_counteruav::fakedata_<ContainerAllocator> >::stream(s, "", v);
return s;
}

} // namespace ros_counteruav

namespace ros
{
namespace message_traits
{



// BOOLTRAITS {'IsFixedSize': True, 'IsMessage': True, 'HasHeader': False}
// {'ros_counteruav': ['/home/project/counterUAV/ROS_system/catkin_ws/src/ros_counteruav/msg'], 'std_msgs': ['/opt/ros/melodic/share/std_msgs/cmake/../msg']}

// !!!!!!!!!!! ['__class__', '__delattr__', '__dict__', '__doc__', '__eq__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_parsed_fields', 'constants', 'fields', 'full_name', 'has_header', 'header_present', 'names', 'package', 'parsed_fields', 'short_name', 'text', 'types']




template <class ContainerAllocator>
struct IsFixedSize< ::ros_counteruav::fakedata_<ContainerAllocator> >
  : TrueType
  { };

template <class ContainerAllocator>
struct IsFixedSize< ::ros_counteruav::fakedata_<ContainerAllocator> const>
  : TrueType
  { };

template <class ContainerAllocator>
struct IsMessage< ::ros_counteruav::fakedata_<ContainerAllocator> >
  : TrueType
  { };

template <class ContainerAllocator>
struct IsMessage< ::ros_counteruav::fakedata_<ContainerAllocator> const>
  : TrueType
  { };

template <class ContainerAllocator>
struct HasHeader< ::ros_counteruav::fakedata_<ContainerAllocator> >
  : FalseType
  { };

template <class ContainerAllocator>
struct HasHeader< ::ros_counteruav::fakedata_<ContainerAllocator> const>
  : FalseType
  { };


template<class ContainerAllocator>
struct MD5Sum< ::ros_counteruav::fakedata_<ContainerAllocator> >
{
  static const char* value()
  {
    return "ad736a2e8818154c487bb80fe42ce43b";
  }

  static const char* value(const ::ros_counteruav::fakedata_<ContainerAllocator>&) { return value(); }
  static const uint64_t static_value1 = 0xad736a2e8818154cULL;
  static const uint64_t static_value2 = 0x487bb80fe42ce43bULL;
};

template<class ContainerAllocator>
struct DataType< ::ros_counteruav::fakedata_<ContainerAllocator> >
{
  static const char* value()
  {
    return "ros_counteruav/fakedata";
  }

  static const char* value(const ::ros_counteruav::fakedata_<ContainerAllocator>&) { return value(); }
};

template<class ContainerAllocator>
struct Definition< ::ros_counteruav::fakedata_<ContainerAllocator> >
{
  static const char* value()
  {
    return "byte data\n"
;
  }

  static const char* value(const ::ros_counteruav::fakedata_<ContainerAllocator>&) { return value(); }
};

} // namespace message_traits
} // namespace ros

namespace ros
{
namespace serialization
{

  template<class ContainerAllocator> struct Serializer< ::ros_counteruav::fakedata_<ContainerAllocator> >
  {
    template<typename Stream, typename T> inline static void allInOne(Stream& stream, T m)
    {
      stream.next(m.data);
    }

    ROS_DECLARE_ALLINONE_SERIALIZER
  }; // struct fakedata_

} // namespace serialization
} // namespace ros

namespace ros
{
namespace message_operations
{

template<class ContainerAllocator>
struct Printer< ::ros_counteruav::fakedata_<ContainerAllocator> >
{
  template<typename Stream> static void stream(Stream& s, const std::string& indent, const ::ros_counteruav::fakedata_<ContainerAllocator>& v)
  {
    s << indent << "data: ";
    Printer<int8_t>::stream(s, indent + "  ", v.data);
  }
};

} // namespace message_operations
} // namespace ros

#endif // ROS_COUNTERUAV_MESSAGE_FAKEDATA_H
