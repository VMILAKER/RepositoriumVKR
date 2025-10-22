import {Card, Collapse} from 'antd'

export function CardVKR(item) {
  // const source = document.querySelector()
  const tag_array = (param) => {
    let final_tag = []
    for (let i in param) {
      final_tag.push(param[i].tag_name)
    }
    return final_tag.join(', ')
  };
  
  return( 
    <Card component='span' title={item?.theme}>
      <div className='flex items-center'><span className='font-bold'>Руководитель: </span><Collapse className='w-130' size='small' items={[{label:item?.supervisor_gqw.name, children: <ul><li>Место работы: {item?.supervisor_gqw.department_gqw.department}</li><li>Учёная степень: {item?.supervisor_gqw.degree_gqw.degree}</li></ul>}]}/></div>
      <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.type_of_qualification.qualification}</p>
      <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
      <p className='my-2'><span className='font-bold'>Ссылка на аннотацию: </span><a className='text-justify' href={`http://10.6.41.116:81/${item?.reference}`} target="_blank" >{item?.reference}</a></p>
      <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tag_gqw)}</p>
    </Card>
  )
}
